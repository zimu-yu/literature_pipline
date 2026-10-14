# download.py

from pathlib import Path

from curl_cffi import requests
from tqdm import tqdm


def download_file(
    url: str,
    save_path: str,
    headers: dict = None,
    retries: int = 3
) -> dict:

    save_path = Path(save_path)
    save_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    last_error = None

    for attempt in range(retries):

        try:
            response = requests.get(
                url,
                headers=headers,
                impersonate="chrome",
                stream=True,
                timeout=120
            )

            response.raise_for_status()

            content_type = (
                response.headers.get(
                    "content-type",
                    ""
                ).lower()
            )

            if (
                save_path.suffix.lower() == ".pdf"
                and "text/html" in content_type
            ):
                raise ValueError(
                    f"Expected PDF but got {content_type}"
                )

            total = int(
                response.headers.get(
                    "content-length",
                    0
                )
            )

            with open(
                save_path,
                "wb"
            ) as f:

                with tqdm(
                    total=total,
                    unit="B",
                    unit_scale=True,
                    desc=save_path.name
                ) as pbar:

                    for chunk in response.iter_content(
                        chunk_size=8192
                    ):

                        if not chunk:
                            continue

                        f.write(chunk)
                        pbar.update(len(chunk))

            size_mb = (
                save_path.stat().st_size
                / (1024 * 1024)
            )

            return {
                "url": url,
                "local_path": str(save_path),
                "size_mb": round(
                    size_mb,
                    2
                ),
                "content_type": content_type,
                "response_headers": dict(
                    response.headers
                ),
            }

        except Exception as e:

            last_error = e

            if save_path.exists():
                save_path.unlink()

            if attempt == retries - 1:
                raise

            print(
                f"Download failed, retrying "
                f"({attempt + 2}/{retries})..."
            )

    raise last_error