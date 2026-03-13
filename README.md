# Data Extraction Workflow

> A professional, reusable automation pattern for external data collection, transformation and structured output generation.

---

## Business Purpose

Many organisations need to routinely collect data from external sources, clean it, and make it available for downstream reporting or analytics.

This workflow demonstrates exactly that pattern:

- Pull structured data from a public API
- Validate and normalise the response
- Export a clean, analysis-ready CSV dataset
- Produce an operations summary log
- Generate a visual chart for quick insight

The same architecture can be adapted for exchange rates, weather feeds, product catalogues, logistics APIs, or any JSON-based data source.

---

## Data Source

**REST Countries API** — `https://restcountries.com/v3.1/region/{region}`

- Public, no authentication required
- Covers all 5 world regions — Africa, Americas, Asia, Europe, Oceania
- Returns ~245 country records with rich structured fields

---

## What the Script Does

| Step | Function | Description |
|------|----------|-------------|
| 1 | `fetch_data()` | HTTP GET requests across all world regions |
| 2 | `validate_response()` | Drops records missing required fields |
| 3 | `transform_data()` | Flattens nested JSON into a clean pandas DataFrame |
| 4 | `save_csv()` | Exports the structured dataset to CSV |
| 5 | `generate_summary()` | Writes a human-readable operations log |
| 6 | `generate_chart()` | Produces a bar chart of the top 15 countries by population |

---

## Outputs

All files are saved inside `output/`:

| File | Description |
|------|-------------|
| `extracted_data.csv` | Full structured dataset, sorted by population |
| `summary.txt` | Operations log with key metrics and insights |
| `chart.png` | Horizontal bar chart — top 15 most populous countries |

### CSV Columns

| Column | Description |
|--------|-------------|
| Country | Common name |
| Official Name | Full official name |
| Region | Continent / region |
| Subregion | Sub-region |
| Capital | Capital city |
| Population | Total population |
| Area (km²) | Land area in square kilometres |
| Currencies | Currency name and ISO code |
| Languages | Official languages |
| Timezones | UTC timezone offsets |
| Independent | Whether the country is independent |

---

## How to Run

**1. Clone the repository and navigate to the project**

```bash
git clone <repo-url>
cd demo_02_data_extraction
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Run the extraction**

```bash
python script/extract_data.py
```

**4. Check the outputs**

```
output/
├── extracted_data.csv
├── summary.txt
└── chart.png
```

---

## Project Structure

```
demo_02_data_extraction/
├── script/
│   └── extract_data.py     # Main extraction script
├── output/                 # Generated output files
├── screenshots/            # Output previews
├── requirements.txt
└── README.md
```

---

## Reusability

This workflow is designed to be extended:

- **Swap the API** — update `API_BASE` and `REGIONS` to point at any JSON endpoint
- **Add scheduling** — wrap `main()` with a cron job or cloud scheduler
- **Connect to storage** — replace `save_csv()` with a database or cloud bucket writer
- **Add alerting** — emit the summary to Slack, email, or a monitoring dashboard

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.11+ | Core language |
| requests | HTTP requests |
| pandas | Data transformation |
| matplotlib | Chart generation |

---

*Built as a portfolio demonstration of a production-ready data extraction pattern.*
