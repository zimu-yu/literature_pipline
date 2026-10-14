# discover/fallbacks/europepmc.py

from curl_cffi import requests


def discover_europepmc(doi: str) -> dict:
    # 1. DOI -> PMCID
    search_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    response = requests.get(
        search_url,
        params={
            "query": f'DOI:"{doi}"',
            "format": "json"
        },
        impersonate="chrome",
        timeout=30
    )
    response.raise_for_status()

    results = response.json()["resultList"]["result"]

    if not results:
        return {
            "source": "Europe PMC",
            "pmcid": None,
            "fulltext_url": None,
            "si_url": None
        }

    pmcid = results[0].get("pmcid")

    if not pmcid:
        return {
            "source": "Europe PMC",
            "pmcid": None,
            "fulltext_url": None,
            "si_url": None
        }

    # 2. 根据 PMCID 构造全文和 SI 地址
    base_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}"

    return {
        "source": "Europe PMC",
        "pmcid": pmcid,
        "fulltext_url": f"{base_url}/fullTextXML",
        "si_url": f"{base_url}/supplementaryFiles"
    }


if __name__ == "__main__":
    doi = "10.1021/acsomega.2c05637"
    print(discover_europepmc(doi))