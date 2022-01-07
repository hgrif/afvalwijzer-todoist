import datetime as dt
import logging
import os
from collections import namedtuple

import requests
from bs4 import BeautifulSoup

IFTTT_URL = "https://maker.ifttt.com/trigger/afvalkalender/json/with/key/"

Collection = namedtuple("Collection", ["when", "what"])


class Parser:
    def __init__(self, page):
        self.soup = BeautifulSoup(page, "html.parser")
        self.year = None
        self.months = {
            "januari": 1,
            "februari": 2,
            "maart": 3,
            "april": 4,
            "mei": 5,
            "juni": 6,
            "juli": 7,
            "augustus": 8,
            "september": 9,
            "oktober": 10,
            "november": 11,
            "december": 12,
        }

    def parse_collections(self):
        container = self.soup.find(class_="ophaaldagen")
        self.year = container.get("id")[-4:]
        dates = container.find_all(class_="span-line-break")
        events = container.find_all(class_="afvaldescr")
        return [self._parse_collection(d, e) for d, e in zip(dates, events)]

    def _parse_collection(self, date, event):
        _, day, month = date.text.split()
        when = dt.date(int(self.year), self.months[month], int(day))
        what = event.text
        return Collection(when, what)


def find_tomorrows_collections(collections):
    tomorrow = dt.date.today() + dt.timedelta(days=1)
    return filter(lambda x: x.when == tomorrow, collections)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    postal_code = os.environ.get("POSTAL_CODE", "3511JK")
    house_number = os.environ.get("HOUSE_NUMBER", 1)
    ifttt_maker_key = os.environ["IFTTT_MAKER_KEY"]
    response = requests.get(
        f"https://www.mijnafvalwijzer.nl/nl/{postal_code}/{house_number}"
    )
    collections = Parser(response.content).parse_collections()
    logger.info("Found %i events", len(collections))
    tomorrow = list(find_tomorrows_collections(collections))
    for collection in tomorrow:
        logger.info("Posting collection")
        response = requests.post(IFTTT_URL + ifttt_maker_key,
                                 json={collection.what: str(collection.when)})
        response.raise_for_status()
