import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://xnxx.com/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 14) "
        "AppleWebKit/537.36 Chrome/130.0.0.0 "
        "Mobile Safari/537.36"
    )
}


def scrape_page(session, url):
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def extract_video_data(data):
    videos = []

    if isinstance(data, dict):

        if data.get("@type") == "VideoObject":
            videos.append({
                "thumbnailUrl": data.get("thumbnailUrl"),
                "duration": data.get("duration"),
                "contentUrl": data.get("contentUrl"),
                "title": data.get("name")
            })

        for value in data.values():
            if isinstance(value, (dict, list)):
                videos.extend(extract_video_data(value))

    elif isinstance(data, list):
        for item in data:
            videos.extend(extract_video_data(item))

    return videos


def get_category(query):
    results = []

    with requests.Session() as session:
        session.headers.update(HEADERS)

        start_url = urljoin(
            BASE_URL.rstrip("/") + "/",
            query.lstrip("/")
        )

        try:
            soup = scrape_page(session, start_url)
        except requests.RequestException:
            return results

        links = []

        for element in soup.select(".thumb"):
            anchor = (
                element
                if element.name == "a" and element.get("href")
                else element.find("a", href=True)
            )

            if anchor and anchor.get("href"):
                links.append(urljoin(start_url, anchor["href"]))

        links = list(dict.fromkeys(links))

        for page_url in links:
            try:
                page = scrape_page(session, page_url)

                scripts = page.find_all(
                    "script",
                    attrs={"type": "application/ld+json"}
                )

                for script in scripts:
                    raw = script.string or script.get_text(strip=True)

                    if not raw:
                        continue

                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    results.extend(extract_video_data(data))

            except requests.RequestException:
                continue

    return results

'''
# Test
data = get_category("/search/todays-selection")

print(json.dumps(data, indent=4, ensure_ascii=False))'''