import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# =========================
# SETTINGS
# =========================

MIN_MARKET_CAP = 1_000_000_000      # $1B

# Example stock universe
tickers = [
    "AAPL", "MSFT", "NVDA", "AMD", "MU",
    "TSLA", "AMZN", "META", "PLTR", "NFLX",
    "GOOGL", "AVGO", "COIN", "SMCI"
]

results = []

# =========================
# FIND NEXT FRIDAY
# =========================

today = datetime.today()
days_until_friday = (4 - today.weekday()) % 7
if days_until_friday == 0:
    days_until_friday = 7
next_friday = today + timedelta(days=days_until_friday)
next_friday_str = next_friday.strftime('%Y-%m-%d')

print(f"Scanning expiry: {next_friday_str}")

# =========================
# MAIN SCAN
# =========================

for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        market_cap = info.get("marketCap", 0)
        if market_cap < MIN_MARKET_CAP:
            continue

        current_price = info.get("currentPrice")
        company_name = info.get("longName", ticker)
        if current_price is None:
            continue

        # Earnings avoidance
        calendar = stock.calendar
        earnings_date = None
        if calendar and 'Earnings Date' in calendar:
            earnings_date = calendar['Earnings Date']
            if isinstance(earnings_date, list) and earnings_date:
                earnings_date = earnings_date[0]
            if earnings_date and earnings_date <= next_friday.date():
                print(f"Skipping {ticker}: Earnings on {earnings_date}")
                continue

        expirations = stock.options
        if next_friday_str not in expirations:
            continue

        option_chain = stock.option_chain(next_friday_str)
        puts = option_chain.puts

        # Strike range: 10-12% below current price
        min_strike = current_price * (1 - 0.12)
        max_strike = current_price * (1 - 0.10)

        filtered_puts = puts[
            (puts['strike'] >= min_strike) &
            (puts['strike'] <= max_strike) &
            (puts['openInterest'] > 0) &
            (puts['volume'] > 0)
        ]

        if not filtered_puts.empty:
            # Select the put with the highest bid (premium)
            best_put = filtered_puts.loc[filtered_puts['bid'].idxmax()]
            strike = best_put['strike']
            premium = best_put['bid']

            results.append({
                "Company_Name": company_name,
                "Current_Stock_Price": round(current_price, 2),
                "ITM_Strike_10_12_percent": round(strike, 2),
                "Premium_Cost": round(premium, 2)
            })

    except Exception as e:
        print(f"Error with {ticker}: {e}")

# =========================
# RESULTS
# =========================

df = pd.DataFrame(results)

if not df.empty:
    output_file = "stock_itm_options_data.xlsx"
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Stock_Options", index=False)
    print(f"Created: {output_file}")
    print(f"Total stocks: {len(df)}")
else:
    print("No data found.")