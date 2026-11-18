import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://xvideos.com"

def scrape_xv(route=""):
    url = urljoin(BASE_URL + "/", route.lstrip("/"))

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    thumbs = soup.find_all("div", class_="thumb-inside")

    for thumb in thumbs:
        a_tag = thumb.find("a")

        if not a_tag or not a_tag.get("href"):
            continue

        page_url = urljoin(BASE_URL + "/", a_tag["href"])

        try:
            page = requests.get(
                page_url,
                headers=headers,
                timeout=20
            )
            page.raise_for_status()

            page_soup = BeautifulSoup(page.text, "html.parser")

            scripts = page_soup.find_all(
                "script",
                type="application/ld+json"
            )

            for script in scripts:
                try:
                    data = json.loads(script.string or script.get_text())

                    items = data if isinstance(data, list) else [data]

                    for item in items:
                        if not isinstance(item, dict):
                            continue

                        entries = item.get("@graph", [item])

                        for entry in entries:
                            if not isinstance(entry, dict):
                                continue

                            yield {
                                "name": entry.get("name"),
                                "thumbnailUrl": entry.get("thumbnailUrl"),
                                "duration": entry.get("duration"),
                                "contentUrl": entry.get("contentUrl")
                            }

                except json.JSONDecodeError:
                    continue

        except requests.RequestException as e:
            print(f"Error scraping {page_url}: {e}")