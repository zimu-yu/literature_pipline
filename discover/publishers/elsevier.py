# discover/publishers/elsevier.py

import os
from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from ..base import PublisherAdapter


class ElsevierAdapter(PublisherAdapter):

    def discover(self, doi: str) -> dict:
        api_key = os.getenv("ELSEVIER_API_KEY")
        landing_url = f"https://doi.org/{doi}"
        soup = BeautifulSoup("", "html.parser")
        try:
            response = requests.get(
                landing_url,
                impersonate="chrome",
                timeout=30
            )
            response.raise_for_status()
            landing_url = response.url
            soup = BeautifulSoup(response.text, "html.parser")
        except Exception:
            if not api_key:
                raise
            # A webpage failure must not prevent an independent API route.
            print("Elsevier landing page unavailable; trying configured API. SI discovery unresolved.")

        candidates = []

        # Elsevier 官方 API

        if api_key:
            api_url = (
                f"https://api.elsevier.com/content/article/doi/{doi}"
            )

            # 先尝试 PDF
            candidates.append({
                "url": api_url,
                "source": "Elsevier",
                "format": "pdf",
                "headers": {
                    "X-ELS-APIKey": api_key,
                    "Accept": "application/pdf"
                }
            })

            # PDF 不行，再尝试 XML
            candidates.append({
                "url": api_url,
                "source": "Elsevier",
                "format": "xml",
                "headers": {
                    "X-ELS-APIKey": api_key,
                    "Accept": "text/xml"
                }
            })

        # 没有 API key 时，尝试网页里的 PDF
        else:
            pdf_meta = soup.find(
                "meta",
                attrs={"name": "citation_pdf_url"}
            )

            if pdf_meta:
                candidates.append({
                    "url": pdf_meta.get("content"),
                    "source": "Elsevier",
                    "format": "pdf",
                    "headers": None
                })

        # SI
        si_urls = []

        for link in soup.find_all("a", href=True):
            href = link["href"]

            if "mmc" in href.lower() or "supplement" in href.lower():
                url = urljoin(landing_url, href)

                if url not in si_urls:
                    si_urls.append(url)

        return {
            "publisher": "Elsevier",
            "landing_url": landing_url,
            "fulltext_candidates": candidates,
            "si_urls": si_urls,
        }
