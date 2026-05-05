# TradingView Company Fetcher

This project fetches `Company_Name`, `Ticker`, and `Industry` data from the TradingView Scanner API for multiple markets and writes the results to an Excel workbook.

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Run

```bash
python fetch_tradingview_companies.py
```

Output file:
- `tradingview_company_ticker_industry_full.xlsx`
