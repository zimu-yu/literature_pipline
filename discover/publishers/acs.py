# discover/publishers/acs.py

from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from ..base import PublisherAdapter


class ACSAdapter(PublisherAdapter):

    def discover(self, doi: str) -> dict:

        landing_url = f"https://pubs.acs.org/doi/{doi}"

        fulltext_candidates = [
            {
                "url": f"https://pubs.acs.org/doi/pdf/{doi}",
                "source": "ACS",
                "format": "pdf",
                "headers": None
            }
        ]

        si_urls = []

        try:
            response = requests.get(
                landing_url,
                impersonate="chrome",
                timeout=30
            )

            response.raise_for_status()

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            landing_url = response.url

            target = (
                f"/doi/suppl/{doi}/suppl_file/"
            ).lower()

            for link in soup.find_all(
                "a",
                href=True
            ):
                href = link["href"]

                if target in href.lower():
                    url = urljoin(
                        landing_url,
                        href
                    )

                    if url not in si_urls:
                        si_urls.append(url)

        except Exception:
            pass

        return {
            "publisher": "ACS",
            "landing_url": landing_url,
            "fulltext_candidates": fulltext_candidates,
            "si_urls": si_urls,
        }