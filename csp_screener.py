import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# =========================
# SETTINGS
# =========================

MIN_MARKET_CAP = 1_000_000_000      # $1B
MIN_PREMIUM_PERCENT = 1.0           # 1%
MAX_DISTANCE_PERCENT = 12           # 12% below stock
MIN_DISTANCE_PERCENT = 10           # 10% below stock
MIN_OPEN_INTEREST = 100
MIN_VOLUME = 10
MAX_BID_ASK_SPREAD_PERCENT = 10     # 10%
MIN_DELTA = 0.20                    # 0.20 delta (ITM)
MAX_DELTA = 0.35                    # 0.35 delta
MIN_IV = 0.4                        # High IV filter (approximating IV Rank >40)

# Example stock universe (can be expanded or loaded from TradingView data)
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
        if current_price is None:
            continue

        # Earnings avoidance: Check if earnings are within the week
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

        # Filter strikes within 10-12% below current price
        min_strike = current_price * (1 - MAX_DISTANCE_PERCENT / 100)
        max_strike = current_price * (1 - MIN_DISTANCE_PERCENT / 100)

        filtered_puts = puts[
            (puts['strike'] >= min_strike) &
            (puts['strike'] <= max_strike) &
            (puts['openInterest'] >= MIN_OPEN_INTEREST) &
            (puts['volume'] >= MIN_VOLUME) &
            (puts['impliedVolatility'] >= MIN_IV)
        ]

        for _, row in filtered_puts.iterrows():
            strike = row['strike']
            bid = row['bid']
            ask = row['ask']
            premium = bid  # Use bid as premium received

            if premium <= 0 or ask <= 0:
                continue

            # Bid/Ask spread
            spread_percent = ((ask - bid) / bid) * 100
            if spread_percent > MAX_BID_ASK_SPREAD_PERCENT:
                continue

            collateral = strike * 100
            premium_received = premium * 100
            premium_percent = (premium_received / collateral) * 100

            if premium_percent < MIN_PREMIUM_PERCENT:
                continue

            distance_percent = ((current_price - strike) / current_price) * 100
            annualized_return = premium_percent * 52  # Weekly to annual

            results.append({
                "Ticker": ticker,
                "Stock Price": round(current_price, 2),
                "Strike": strike,
                "Premium": round(premium, 2),
                "Premium $": round(premium_received, 2),
                "Collateral": round(collateral, 2),
                "Premium %": round(premium_percent, 2),
                "Distance %": round(distance_percent, 2),
                "Annualized %": round(annualized_return, 2),
                "IV": round(row['impliedVolatility'], 2),
                "Spread %": round(spread_percent, 2),
                "OI": row['openInterest'],
                "Volume": row['volume'],
                "Expiry": next_friday_str
            })

    except Exception as e:
        print(f"Error with {ticker}: {e}")

# =========================
# RESULTS
# =========================

df = pd.DataFrame(results)

if not df.empty:
    df = df.sort_values(by="Premium %", ascending=False)
    print("\n===== CASH SECURED PUT OPPORTUNITIES =====\n")
    print(df.to_string(index=False))
else:
    print("No opportunities found.")