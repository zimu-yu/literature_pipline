# discover/crossref.py

from curl_cffi import requests


def get_metadata(doi: str) -> dict:
    url = f"https://api.crossref.org/works/{doi}"

    response = requests.get(
        url,
        impersonate="chrome",
        timeout=30
    )
    response.raise_for_status()

    data = response.json()["message"]

    return {
        "publisher": data.get("publisher"),
        "title": data.get("title", [""])[0]
    }


if __name__ == "__main__":
    print(get_metadata("10.1021/acsomega.2c05637"))