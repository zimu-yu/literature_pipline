# discover/publishers/springer.py

from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from ..base import PublisherAdapter


class SpringerAdapter(PublisherAdapter):

    def discover(self, doi: str) -> dict:
        landing_url = f"https://link.springer.com/article/{doi}"

        response = requests.get(
            landing_url,
            impersonate="chrome",
            timeout=30
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        fulltext_url = f"https://link.springer.com/content/pdf/{doi}.pdf"
        si_urls = []

        for link in soup.find_all("a", href=True):
            href = link["href"]

            if "MOESM" in href or "supplementary" in href.lower():
                url = urljoin(response.url, href)

                if url not in si_urls:
                    si_urls.append(url)

        return {
            "publisher": "Springer",
            "landing_url": response.url,
            "fulltext_url": fulltext_url,
            "si_urls": si_urls,
        }