# Literature Acquisition Pipeline

A small DOI-based literature acquisition pipeline supporting four publishers:

- ACS
- Elsevier
- Springer
- Wiley

The pipeline takes a DOI, identifies the publisher, discovers available full text, tries fallback sources when needed, downloads and validates the files, and records the result in a manifest.

## Installation

Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```


## Optional API Keys

Some routes can use API keys or configuration values.

```bash
export UNPAYWALL_EMAIL="your_email@example.com"
export ELSEVIER_API_KEY="your_key"
export WILEY_API_KEY="your_key"
export SEMANTIC_SCHOLAR_API_KEY="your_key"
```

Do not commit API keys or credentials to GitHub.

## Usage

### Run one DOI

```bash
python run.py 10.1021/acsomega.2c05637
```

DOI URLs are also supported:

```bash
python run.py https://doi.org/10.1021/acsomega.2c05637
```

### Run multiple DOIs

```bash
python run.py \
10.1021/acsomega.2c05637 \
10.1016/j.xcrp.2021.100620
```

### Run a DOI list

Put one DOI per line in a text file:

```text
10.1021/acsomega.2c05637
10.1016/j.xcrp.2021.100620
10.1002/advs.202102156
```

Then run:

```bash
python run.py --file dois_24.txt
```

A failed DOI does not stop the remaining batch.

## Acquisition Flow

The current full-text search order is:

```text
Publisher
→ Unpaywall
→ Europe PMC
→ OpenAlex
→ OSTI
→ Semantic Scholar
→ Crossref TDM
```

PDF is preferred. XML is only used as a fallback.

## Output

Results are saved under:

```text
output/<doi>/
```

For example:

```text
output/
└── 10.1021_acsomega.2c05637/
    ├── article.pdf
    ├── article.xml
    ├── SI/
    └── manifest.json
```

The manifest records the publisher, source, download attempts, validation results, supplementary files, and final status.

## Evaluation

After running the DOI set:

```bash
python evaluate.py
```

The evaluator reports metrics such as:

- full-text acquisition rate
- PDF acquisition rate
- XML fallback rate
- publisher-level performance
- acquisition routes
- failed articles

## Notes

This project does not bypass publisher access controls.

Downloads may fail because of paywalls, API entitlement, institutional authentication requirements, HTTP 403 responses, or unavailable public copies.

Downloaded article files should generally not be committed to GitHub.
