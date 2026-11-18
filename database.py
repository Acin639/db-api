import os
import requests

from dotenv import load_dotenv

load_dotenv()

PB_URL = os.getenv("PB_URL", "").rstrip("/")
PB_EMAIL = os.getenv("PB_EMAIL")
PB_PASSWORD = os.getenv("PB_PASSWORD")

session = requests.Session()


def connect():

    response = session.post(
        f"{PB_URL}/api/collections/_superusers/auth-with-password",
        json={
            "identity": PB_EMAIL,
            "password": PB_PASSWORD
        },
        timeout=30
    )

    response.raise_for_status()

    token = response.json()["token"]

    session.headers.update({
        "Authorization": token
    })


def create_collection(name, category=False):

    # Check whether collection already exists
    check = session.get(
        f"{PB_URL}/api/collections/{name}",
        timeout=30
    )

    if check.status_code == 200:
        print(f"Collection '{name}' already exists.")
        return

    fields = [
        {
            "name": "title",
            "type": "text",
            "required": True
        },
        {
            "name": "thumbnailUrl",
            "type": "text"
        },
        {
            "name": "contentUrl",
            "type": "text",
            "required": True
        },
        {
            "name": "duration",
            "type": "text"
        },
        {
            "name": "views",
            "type": "text"
        }
    ]

    if category:
        fields.append({
            "name": "category",
            "type": "text",
            "required": True
        })

        index = (
            "CREATE UNIQUE INDEX idx_categories_unique "
            "ON categories (title, contentUrl, category)"
        )
    else:
        index = (
            f"CREATE UNIQUE INDEX idx_{name}_unique "
            f"ON {name} (title, contentUrl)"
        )

    payload = {
        "name": name,
        "type": "base",
        "fields": fields,
        "indexes": [index],
        "listRule": "",
        "viewRule": "",
        "createRule": None,
        "updateRule": None,
        "deleteRule": None
    }

    response = session.post(
        f"{PB_URL}/api/collections",
        json=payload,
        timeout=30
    )

    if not response.ok:
        print("Collection creation failed:", response.text)
        response.raise_for_status()

    print(f"Collection '{name}' created successfully.")

def setup_database():

    connect()

    create_collection("home")
    create_collection("shorts")
    create_collection("categories", category=True)


def get_existing(collection):

    existing = set()
    page = 1

    while True:

        response = session.get(
            f"{PB_URL}/api/collections/{collection}/records",
            params={
                "page": page,
                "perPage": 500,
                "fields": "title,contentUrl,category"
            },
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        for item in data["items"]:

            existing.add((
                item.get("title", ""),
                item.get("contentUrl", ""),
                item.get("category", "")
            ))

        if page >= data["totalPages"]:
            break

        page += 1

    return existing


def save_records(collection, records):

    existing = get_existing(collection)

    saved = 0
    duplicates = 0

    for item in records:

        title = item.get("title", "")
        video = item.get("contentUrl", "")
        category = item.get("category", "")

        if not title or not video:
            continue

        key = (title, video, category)

        if key in existing:
            duplicates += 1
            continue

        response = session.post(
            f"{PB_URL}/api/collections/{collection}/records",
            json=item,
            timeout=30
        )

        if response.status_code == 400:
            duplicates += 1
            continue

        response.raise_for_status()

        existing.add(key)
        saved += 1

    return {
        "saved": saved,
        "duplicates": duplicates
    }