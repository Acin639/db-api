import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://twerkqueens.com"


def scrape_shorts(page="/"):
    url = urljoin(BASE_URL, page)

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    items = soup.find_all("div", class_="item-col")

    results = []

    for item in items:
        img = item.find("img")
        title = item.find("span", class_="title")
        duration = item.find("span", class_="tq-dur")
        views = item.find("span", class_=["i-elem", "item-views"])

        video = item.get("data-video")

        image = (
            urljoin(BASE_URL, img.get("src"))
            if img and img.get("src")
            else None
        )

        # Skip items without video or image
        if not video or not image:
            continue

        data = {
            "video": video,
            "image": image,
            "title": title.get_text(strip=True) if title else None,
            "duration": duration.get_text(strip=True) if duration else None,
            "views": views.get_text(strip=True) if views else None
        }

        results.append(data)

    return results


