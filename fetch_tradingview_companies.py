import time
import requests
import pandas as pd

# Only USA / America market
MARKET = "america"

# Required TradingView columns
COLUMNS = ["name", "description", "industry"]

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Origin": "https://www.tradingview.com",
    "Referer": "https://www.tradingview.com/screener/",
}

# Sector → Industry mapping
SECTOR_INDUSTRY_MAP = {
    "Electronic Technology": [
        "Semiconductors", "Telecommunications Equipment", "Aerospace & Defense",
        "Computer Peripherals", "Electronic Components", "Electronic Production Equipment",
        "Computer Processing Hardware", "Electronic Equipment/Instruments",
        "Computer Communications"
    ],
    "Technology Services": [
        "Internet Software/Services", "Packaged Software",
        "Information Technology Services", "Data Processing Services"
    ],
    "Finance": [
        "Major Banks", "Property/Casualty Insurance", "Finance/Rental/Leasing",
        "Real Estate Investment Trusts", "Investment Managers",
        "Investment Banks/Brokers", "Regional Banks", "Multi-Line Insurance",
        "Insurance Brokers/Services", "Life/Health Insurance",
        "Financial Conglomerates", "Real Estate Development",
        "Specialty Insurance", "Savings Banks"
    ],
    "Health Technology": [
        "Pharmaceuticals: Major", "Medical Specialties", "Biotechnology",
        "Pharmaceuticals: Other", "Pharmaceuticals: Generic"
    ],
    "Retail Trade": [
        "Internet Retail", "Specialty Stores", "Home Improvement Chains",
        "Apparel/Footwear Retail", "Department Stores", "Drugstore Chains",
        "Food Retail", "Discount Stores", "Electronics/Appliance Stores",
        "Catalog/Specialty Distribution"
    ],
    "Producer Manufacturing": [
        "Industrial Machinery", "Electrical Products",
        "Trucks/Construction/Farm Machinery", "Auto Parts: OEM",
        "Building Products", "Industrial Conglomerates", "Metal Fabrication",
        "Miscellaneous Manufacturing", "Office Equipment/Supplies"
    ],
    "Energy Minerals": [
        "Integrated Oil", "Oil & Gas Production", "Oil Refining/Marketing", "Coal"
    ],
    "Consumer Non-Durables": [
        "Household/Personal Care", "Beverages: Non-Alcoholic", "Tobacco",
        "Food: Specialty/Candy", "Beverages: Alcoholic", "Apparel/Footwear",
        "Food: Meat/Fish/Dairy", "Food: Major Diversified", "Consumer Sundries"
    ],
    "Utilities": [
        "Electric Utilities", "Gas Distributors", "Water Utilities",
        "Alternative Power Generation"
    ],
    "Consumer Durables": [
        "Motor Vehicles", "Homebuilding", "Recreational Products",
        "Tools & Hardware", "Electronics/Appliances", "Home Furnishings",
        "Automotive Aftermarket", "Other Consumer Specialties"
    ],
    "Non-Energy Minerals": [
        "Precious Metals", "Other Metals/Minerals", "Steel",
        "Construction Materials", "Aluminum", "Forest Products"
    ],
    "Consumer Services": [
        "Restaurants", "Hotels/Resorts/Cruise lines", "Movies/Entertainment",
        "Other Consumer Services", "Cable/Satellite TV", "Casinos/Gaming",
        "Broadcasting", "Publishing: Newspapers",
        "Publishing: Books/Magazines", "Media Conglomerates"
    ],
    "Industrial Services": [
        "Oil & Gas Pipelines", "Engineering & Construction",
        "Environmental Services", "Contract Drilling",
        "Oilfield Services/Equipment"
    ],
    "Transportation": [
        "Railroads", "Air Freight/Couriers", "Other Transportation",
        "Airlines", "Trucking", "Marine Shipping"
    ],
    "Process Industries": [
        "Chemicals: Specialty", "Agricultural Commodities/Milling",
        "Industrial Specialties", "Containers/Packaging",
        "Chemicals: Agricultural", "Chemicals: Major Diversified",
        "Pulp & Paper", "Textiles"
    ],
    "Commercial Services": [
        "Miscellaneous Commercial Services", "Financial Publishing/Services",
        "Advertising/Marketing Services", "Commercial Printing/Forms",
        "Personnel Services"
    ],
    "Communications": [
        "Wireless Telecommunications", "Major Telecommunications",
        "Specialty Telecommunications"
    ],
    "Health Services": [
        "Managed Health Care", "Medical/Nursing Services",
        "Hospital/Nursing Management", "Services to the Health Industry"
    ],
    "Distribution Services": [
        "Wholesale Distributors", "Medical Distributors",
        "Food Distributors", "Electronics Distributors"
    ],
    "Miscellaneous": [
        "Investment Trusts/Mutual Funds", "Miscellaneous"
    ],
}

# Reverse mapping: Industry → Sector
INDUSTRY_TO_SECTOR = {
    industry: sector
    for sector, industries in SECTOR_INDUSTRY_MAP.items()
    for industry in industries
}


def fetch_usa_companies(step: int = 1000) -> list[dict]:
    endpoint = f"https://scanner.tradingview.com/{MARKET}/scan"
    all_rows = []
    start = 0

    while True:
        payload = {
            "columns": COLUMNS,
            "range": [start, start + step],
            "sort": {"sortBy": "name", "sortOrder": "asc"},
            "options": {"lang": "en"},
        }

        response = requests.post(endpoint, json=payload, headers=HEADERS, timeout=30)
        response.raise_for_status()
        result = response.json()

        rows = result.get("data", [])
        if not rows:
            break

        for item in rows:
            values = item.get("d", [])

            if len(values) >= 3:
                ticker = values[0]
                company_name = values[1]
                industry = values[2]

                # Keep only industries from approved mapping
                if industry in INDUSTRY_TO_SECTOR:
                    all_rows.append({
                        "Ticker": ticker,
                        "Company_Name": company_name,
                        "Industry": industry,
                        "Sector": INDUSTRY_TO_SECTOR[industry],
                    })

        start += step
        total = result.get("totalCount")

        if total is not None and start >= total:
            break

        time.sleep(0.25)

    return all_rows


def main():
    print("Fetching USA companies from TradingView...")

    rows = fetch_usa_companies()

    if not rows:
        raise RuntimeError("No USA company data returned from TradingView.")

    df = pd.DataFrame(rows)

    # Final required fields only
    df = df[["Ticker", "Company_Name", "Industry", "Sector"]]

    # Clean and remove duplicates
    df = df.dropna()
    df = df.drop_duplicates()
    df = df.sort_values(by=["Sector", "Industry", "Ticker"])

    output_file = "usa_company_ticker_industry_sector_tradingview.xlsx"

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="USA_Companies", index=False)

    print(f"Created: {output_file}")
    print(f"Total rows: {len(df):,}")


if __name__ == "__main__":
    main()
