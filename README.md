# Ecommerce Scraper

This script scrapes an e-commerce website and exports product details in JSON Lines format. It uses Playwright to
automate the browser interactions and handle the scraping process.

## Requirements

- Python 3.x
- Playwright

## Setup

1. Install the dependencies:

```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:

```bash
playwright install
```

## Usage

```bash
python scraper.py
```

## Output

The scraped product data is stored in the file products.jsonl in JSON Lines format.

## Logs

Logs are saved to scraper.log for debugging purposes.
