import requests
import json

from bs4 import BeautifulSoup
from urllib.parse import urljoin


BASE_URL = "https://xvideos.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def extract_jsonld(soup):

    results = []

    for script in soup.find_all(
        "script",
        type="application/ld+json"
    ):

        try:
            raw = script.string or script.get_text()

            if not raw.strip():
                continue

            data = json.loads(raw)

            items = data if isinstance(data, list) else [data]

            for item in items:

                if not isinstance(item, dict):
                    continue

                graph = item.get("@graph", [item])

                if isinstance(graph, dict):
                    graph = [graph]

                for entry in graph:

                    if isinstance(entry, dict):
                        results.append(entry)

        except (json.JSONDecodeError, TypeError) as error:
            print(f"JSON-LD error: {error}")

    return results


def scrape_xv(route=""):

    results = []

    url = urljoin(
        BASE_URL.rstrip("/") + "/",
        route.lstrip("/")
    )

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

    except requests.RequestException as error:
        print(f"Listing error: {error}")
        return results

    soup = BeautifulSoup(response.text, "html.parser")

    thumbs = soup.find_all(
        "div",
        class_="thumb-inside"
    )

    for thumb in thumbs:

        a_tag = thumb.find("a", href=True)

        if not a_tag:
            continue

        page_url = urljoin(
            BASE_URL.rstrip("/") + "/",
            a_tag["href"]
        )

        try:
            page = requests.get(
                page_url,
                headers=HEADERS,
                timeout=30
            )

            page.raise_for_status()

            page_soup = BeautifulSoup(
                page.text,
                "html.parser"
            )

            entries = extract_jsonld(page_soup)

            for entry in entries:

                title = entry.get("name")

                thumbnail = (
                    entry.get("thumbnailUrl")
                    or entry.get("image")
                )

                if isinstance(thumbnail, list):
                    thumbnail = thumbnail[0] if thumbnail else None

                if isinstance(thumbnail, dict):
                    thumbnail = thumbnail.get("url")

                video = (
                    entry.get("contentUrl")
                    or entry.get("embedUrl")
                )

                duration = entry.get("duration") or ""

                if not title or not thumbnail or not video:
                    continue

                results.append({
                    "title": title.strip(),
                    "thumbnailUrl": thumbnail,
                    "contentUrl": video,
                    "duration": duration,
                    "views": ""
                })

        except requests.RequestException as error:
            print(f"Page scraping error ({page_url}): {error}")

        except Exception as error:
            print(f"Unexpected scraping error: {error}")

    return results