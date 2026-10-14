# discover/publishers/wiley.py

import os

from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote

from ..base import PublisherAdapter


class WileyAdapter(PublisherAdapter):

    def discover(self, doi: str) -> dict:

        # 论文官方页面
        api_key = os.getenv("WILEY_API_KEY")
        landing_url = f"https://onlinelibrary.wiley.com/doi/{doi}"
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
            print("Wiley landing page unavailable; trying configured API. SI discovery unresolved.")

        candidates = []

        # =====================================================
        # Wiley TDM API
        # =====================================================


        if api_key:

            api_url = (
                "https://api.wiley.com/"
                "onlinelibrary/tdm/v1/articles/"
                + quote(doi, safe="")
            )

            # 不自动跟 redirect
            api_response = requests.get(
                api_url,
                headers={
                    "Wiley-TDM-Client-Token": api_key
                },
                impersonate="chrome",
                allow_redirects=False,
                timeout=30
            )

            # Wiley API 通常返回 302，
            # Location 是真正的临时 PDF 地址
            if api_response.status_code in (
                301, 302, 303, 307, 308
            ):

                pdf_url = api_response.headers.get(
                    "Location"
                )

                if pdf_url:

                    candidates.append({
                        "url": pdf_url,
                        "source": "Wiley",
                        "format": "pdf",
                        "headers": None
                    })

            # 如果 API 直接返回 200，也尝试直接作为 PDF
            elif api_response.status_code == 200:

                candidates.append({
                    "url": api_url,
                    "source": "Wiley",
                    "format": "pdf",
                    "headers": {
                        "Wiley-TDM-Client-Token":
                            api_key
                    }
                })

        # =====================================================
        # 没有 API candidate 时，
        # 再尝试网页里的普通 PDF
        # =====================================================

        if not candidates:

            pdf_meta = soup.find(
                "meta",
                attrs={
                    "name": "citation_pdf_url"
                }
            )

            if pdf_meta:

                pdf_url = pdf_meta.get(
                    "content"
                )

                candidates.append({
                    "url": pdf_url,
                    "source": "Wiley",
                    "format": "pdf",
                    "headers": None
                })

        # =====================================================
        # SI
        # =====================================================

        si_urls = []

        for link in soup.find_all(
            "a",
            href=True
        ):

            href = link["href"]

            if "downloadSupplement" in href:

                url = urljoin(
                    landing_url,
                    href
                )

                if url not in si_urls:
                    si_urls.append(url)

        return {
            "publisher": "Wiley",
            "landing_url": landing_url,
            "fulltext_candidates": candidates,
            "si_urls": si_urls,
        }
