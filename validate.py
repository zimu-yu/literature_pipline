# validate.py

from pathlib import Path
from xml.etree import ElementTree

from pypdf import PdfReader


def validate_file(path: str) -> bool:

    path = Path(path)

    if (
        not path.exists()
        or path.stat().st_size == 0
    ):
        return False

    # PDF：检查文件头
    if path.suffix.lower() == ".pdf":

        with open(path, "rb") as f:

            return (
                f.read(4)
                == b"%PDF"
            )

    # XML：检查是否能正常解析
    if path.suffix.lower() == ".xml":

        try:

            ElementTree.parse(path)

            return True

        except ElementTree.ParseError:

            return False

    # 其他 SI 文件
    return True


def validate_article(
    path: str,
    doi: str
) -> bool:

    if not validate_file(path):
        return False

    path = Path(path)

    # ==================================================
    # PDF
    # ==================================================

    if path.suffix.lower() == ".pdf":

        reader = PdfReader(path)

        text = "".join(
            page.extract_text() or ""
            for page in reader.pages[:3]
        )

        return (
            doi.lower()
            in text.lower()
        )

    # ==================================================
    # XML
    # ==================================================

    if path.suffix.lower() == ".xml":

        # 太小的 XML 通常只是 metadata，
        # 不太可能是完整论文正文。
        if path.stat().st_size < 10_000:
            return False

        text = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        lower_text = text.lower()

        # Elsevier 未授权时可能返回
        # minimized metadata，而不是完整正文。
        if (
            "minimized metadata response"
            in lower_text
        ):
            return False

        # 最后确认 XML 与目标 DOI 对应
        return (
            doi.lower()
            in lower_text
        )

    return False


def validate_si(
    path: str,
    source_url: str,
    doi: str,
    source: str,
    pmcid: str = None
) -> bool:

    if not validate_file(path):
        return False

    if (
        doi.lower()
        in source_url.lower()
    ):
        return True

    if (
        source == "Europe PMC"
        and pmcid
    ):

        return (
            pmcid.lower()
            in source_url.lower()
        )

    return False


def validate_si_complete(
    si_urls: list,
    downloaded_si: list
) -> bool:

    if not si_urls:
        return True

    if not downloaded_si:
        return False

    return all(
        item["valid"]
        for item in downloaded_si
    )