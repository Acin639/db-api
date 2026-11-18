from concurrent.futures import ThreadPoolExecutor, as_completed

from xv import scrape_xv
from xn import get_category
from ww2 import gethome as gethome_ww2


def gethome():

    tasks = [
        (scrape_xv, "/"),
        (get_category, "/todays-selection"),
        (gethome_ww2, 10)
    ]

    results = []
    seen_titles = set()

    with ThreadPoolExecutor(max_workers=3) as executor:

        futures = [
            executor.submit(func, arg)
            for func, arg in tasks
        ]

        for future in as_completed(futures):

            try:
                data = future.result()

                if not data:
                    continue

                for item in data:

                    title = item.get("title") or item.get("name")

                    if not title:
                        continue

                    unique_title = title.strip().lower()

                    if unique_title not in seen_titles:
                        seen_titles.add(unique_title)
                        results.append(item)

            except Exception as e:
                print(f"Scraping error: {e}")

    return results

'''
home = gethome()

print(home)'''