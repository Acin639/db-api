from flask import Flask, jsonify
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from home_merge_db import gethome as scrape_home
from shorts import scrape_shorts as get_shorts
from xn import get_category
from flask_cors import CORS
from database import setup_database, save_records



app = Flask(__name__)
@app.route("/health")
def health():
    return jsonify({
        "status": "online",
        "message": "Flask server is running"
    })
setup_database()

CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

CATEGORIES = [
    "lesbian",
    "gay",
    "ebony",
    "transgender",
    "family",
    "stepmom",
    "bbw",
    "bbc",
    "blowjob"
]

MAX_WORKERS = 5

refresh_lock = Lock()


def normalize(item, category=None):

    title = item.get("title") or item.get("name")

    thumbnail = (
        item.get("thumbnailUrl")
        or item.get("image")
    )

    video = (
        item.get("contentUrl")
        or item.get("videourl")
        or item.get("video")
    )

    if not title or not video:
        return None

    result = {
        "title": title,
        "thumbnailUrl": thumbnail or "",
        "contentUrl": video,
        "duration": item.get("duration") or "",
        "views": str(item.get("views") or "")
    }

    if category is not None:
        result["category"] = category

    return result


def get_results(data):

    if data is None:
        return []

    if isinstance(data, dict):
        return [data]

    return list(data)


def run_scrapers():

    tasks = [
        ("home", scrape_home, (10,), None),
        ("shorts", get_shorts, (), None)
    ]

    for category in CATEGORIES:

        tasks.append((
            "categories",
            get_category,
            (category,),
            category
        ))

    results = {
        "home": [],
        "shorts": [],
        "categories": []
    }

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        futures = {
            executor.submit(func, *args): (collection, category)
            for collection, func, args, category in tasks
        }

        for future in as_completed(futures):

            collection, category = futures[future]

            try:
                data = get_results(future.result())

                for item in data:

                    if not isinstance(item, dict):
                        continue

                    cleaned = normalize(item, category)

                    if cleaned:
                        results[collection].append(cleaned)

            except Exception as error:
                print(f"{collection} scraping error: {error}")

    return results


@app.route("/api/home", methods=["GET"])
def home():

    if not refresh_lock.acquire(blocking=False):

        return jsonify({
            "success": False,
            "message": "A database update is already running."
        }), 409

    try:

        results = run_scrapers()

        stats = {}

        for collection, records in results.items():

            stats[collection] = save_records(
                collection,
                records
            )

        return jsonify({
            "success": True,
            "message": "PocketBase updated successfully.",
            "results": stats
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500

    finally:
        refresh_lock.release()


if __name__ == "__main__":

    

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )