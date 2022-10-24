import json
import re
from datetime import date, datetime

import requests
from pyquery import PyQuery

# from rich import print


def parse_occupations(items):
    occupations = []

    for item in items:
        occupied = bool(item.get("backgroundColor"))
        if not occupied:
            continue
        day = item["start"].partition(" ")[0]

        occupations.append(datetime.strptime(day, "%Y-%m-%d"))

    return sorted(occupations)


def scrap_item(url):
    print(f"Processing {url}")
    item = {"url": url}

    response = requests.get(
        url,
        headers={
            "authority": "www.sanmatiaspropiedades.com.ar",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
        },
    )
    response.raise_for_status()
    pq = PyQuery(response.content)

    item["id"], _, item["name"] = re.split(r"(\-| ?– ?)", pq("h1.header_title").text())

    prices = json.loads(pq("div.ovabrw__product_calendar").attr("price_calendar"))

    item["price"] = PyQuery(prices[1]["ovabrw_daily_monday"]).text()

    special_prices = json.loads(
        pq("div.ovabrw__product_calendar").attr("data-special-time")
    )
    item["special_prices"] = {
        PyQuery(k).text(): tuple(
            date.fromtimestamp(int(timestamp)).strftime("%Y-%m-%d") for timestamp in v
        )
        for (k, v) in special_prices.items()
    }
    try:
        occupations = json.loads(pq("div.ovabrw__product_calendar").attr("order_time"))
        occupations = parse_occupations(occupations)
    except json.decoder.JSONDecodeError:
        print(f" nothing occupied")
        occupations = []

    item["occupation"] = occupations
    return item


def get_apartments_urls():

    headers = {
        "authority": "www.sanmatiaspropiedades.com.ar",
        "accept": "*/*",
        "accept-language": "es-US,es;q=0.9,es-419;q=0.8,en;q=0.7,en-US;q=0.6",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "dnt": "1",
        "origin": "https://www.sanmatiaspropiedades.com.ar",
        "referer": "https://www.sanmatiaspropiedades.com.ar/alquiler/",
        "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }

    data = {
        "action": "ovabrw_search_map",
        "start_date": "",
        "end_date": "",
        "adults": "1",
        "childrens": "1",
        "beds": "1",
        "order": "DESC",
        "orderby": "date",
        "per_page": "100",
        "booking_on_page": "no",
        "taxonomies": "[]",
    }

    response = requests.post(
        "https://www.sanmatiaspropiedades.com.ar/wp-admin/admin-ajax.php",
        headers=headers,
        data=data,
    )

    return sorted(
        {
            e.attrib["href"].partition("?")[0]
            for e in PyQuery(response.json()["result"])("a")
        }
    )


if __name__ == "__main__":

    items = [scrap_item(url) for url in get_apartments_urls()]
    json.dump(
        items,
        open("sanmatiaspropiedades.json", "w"),
        indent=2,
        default=lambda a: str(a).partition(" ")[0],
    )
