"""
Data Extraction Workflow
========================
Source: REST Countries API (https://restcountries.com)
Purpose: Automated extraction, transformation and export of country data
         for reporting and analytics pipelines.
"""

import requests
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE = "https://restcountries.com/v3.1/region"
REGIONS = ["africa", "americas", "asia", "europe", "oceania"]
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
CSV_FILE = os.path.join(OUTPUT_DIR, "extracted_data.csv")
SUMMARY_FILE = os.path.join(OUTPUT_DIR, "summary.txt")
CHART_FILE = os.path.join(OUTPUT_DIR, "chart.png")

FIELDS_TO_EXTRACT = [
    "name",
    "region",
    "subregion",
    "population",
    "area",
    "capital",
    "currencies",
    "languages",
    "timezones",
    "independent",
]


# ---------------------------------------------------------------------------
# Step 1 – Fetch
# ---------------------------------------------------------------------------

def fetch_data(base: str = API_BASE, regions: list[str] = REGIONS) -> list[dict]:
    """Request raw country data from the REST Countries API (per region)."""
    all_records: list[dict] = []
    for region in regions:
        url = f"{base}/{region}"
        print(f"[fetch]     GET {url}")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        batch = response.json()
        print(f"[fetch]       └─ {len(batch)} records ({region})")
        all_records.extend(batch)
    print(f"[fetch]     Total: {len(all_records)} records received")
    return all_records


# ---------------------------------------------------------------------------
# Step 2 – Validate
# ---------------------------------------------------------------------------

def validate_response(data: list[dict]) -> list[dict]:
    """Keep only records that contain the minimum required fields."""
    required = {"name", "region", "population"}
    valid = [r for r in data if required.issubset(r.keys())]
    dropped = len(data) - len(valid)
    if dropped:
        print(f"[validate]  {dropped} incomplete record(s) dropped")
    print(f"[validate]  {len(valid)} valid records")
    return valid


# ---------------------------------------------------------------------------
# Step 3 – Transform
# ---------------------------------------------------------------------------

def _safe_get(record: dict, *keys, default="N/A"):
    """Traverse nested keys safely."""
    node = record
    for key in keys:
        if not isinstance(node, dict):
            return default
        node = node.get(key, default)
        if node == default:
            return default
    return node if node else default


def transform_data(data: list[dict]) -> pd.DataFrame:
    """Normalise raw records into a flat, clean DataFrame."""
    rows = []
    for record in data:
        row = {
            "Country":          _safe_get(record, "name", "common"),
            "Official Name":    _safe_get(record, "name", "official"),
            "Region":           record.get("region", "N/A"),
            "Subregion":        record.get("subregion", "N/A"),
            "Capital":          (record.get("capital") or ["N/A"])[0],
            "Population":       record.get("population", 0),
            "Area (km²)":       record.get("area", 0),
            "Currencies":       ", ".join(
                                    f"{v.get('name','?')} ({k})"
                                    for k, v in (record.get("currencies") or {}).items()
                                ) or "N/A",
            "Languages":        ", ".join(
                                    sorted((record.get("languages") or {}).values())
                                ) or "N/A",
            "Timezones":        ", ".join(record.get("timezones") or []) or "N/A",
            "Independent":      record.get("independent", False),
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df["Population"]  = pd.to_numeric(df["Population"],  errors="coerce").fillna(0).astype(int)
    df["Area (km²)"]  = pd.to_numeric(df["Area (km²)"],  errors="coerce").fillna(0).astype(float)
    df.sort_values("Population", ascending=False, inplace=True)
    df.reset_index(drop=True, inplace=True)

    print(f"[transform] DataFrame shape: {df.shape}")
    return df


# ---------------------------------------------------------------------------
# Step 4 – Save CSV
# ---------------------------------------------------------------------------

def save_csv(df: pd.DataFrame, path: str = CSV_FILE) -> None:
    """Persist the cleaned DataFrame as a UTF-8 CSV file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"[save_csv]  Saved → {path}")


# ---------------------------------------------------------------------------
# Step 5 – Generate Summary
# ---------------------------------------------------------------------------

def generate_summary(df: pd.DataFrame, path: str = SUMMARY_FILE) -> None:
    """Write a human-readable operations log to a text file."""
    total_pop        = df["Population"].sum()
    avg_area         = df["Area (km²)"].replace(0, float("nan")).mean()
    most_pop_country = df.iloc[0]["Country"] if not df.empty else "N/A"
    most_pop_value   = df.iloc[0]["Population"] if not df.empty else 0
    regions          = df["Region"].value_counts().to_dict()

    summary_lines = [
        "=" * 60,
        "  DATA EXTRACTION WORKFLOW — SUMMARY REPORT",
        "=" * 60,
        "",
        f"  Run timestamp : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"  Data source   : REST Countries API (restcountries.com/v3.1/region/...)",
        f"  Records found : {len(df)}",
        "",
        "  --- Global Insights ---",
        f"  Total world population  : {total_pop:,}",
        f"  Average country area    : {avg_area:,.1f} km²",
        f"  Most populous country   : {most_pop_country} ({most_pop_value:,})",
        "",
        "  --- Countries per Region ---",
    ]
    for region, count in sorted(regions.items(), key=lambda x: -x[1]):
        summary_lines.append(f"    {region:<20} {count:>4} countries")

    summary_lines += [
        "",
        "  --- Output Files ---",
        f"  extracted_data.csv  — full structured dataset",
        f"  summary.txt         — this report",
        f"  chart.png           — top 15 countries by population",
        "",
        "=" * 60,
    ]

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))

    print(f"[summary]   Saved → {path}")


# ---------------------------------------------------------------------------
# Step 6 – Generate Chart
# ---------------------------------------------------------------------------

def generate_chart(df: pd.DataFrame, path: str = CHART_FILE) -> None:
    """Produce a horizontal bar chart of the top 15 countries by population."""
    top15 = df.head(15).copy()
    top15["Population (M)"] = top15["Population"] / 1_000_000

    fig, ax = plt.subplots(figsize=(12, 7))

    colors = plt.cm.viridis([i / len(top15) for i in range(len(top15))])
    bars = ax.barh(top15["Country"], top15["Population (M)"], color=colors)

    ax.invert_yaxis()
    ax.set_xlabel("Population (millions)", fontsize=12, labelpad=10)
    ax.set_title("Top 15 Most Populous Countries", fontsize=16, fontweight="bold", pad=15)

    for bar, val in zip(bars, top15["Population (M)"]):
        ax.text(
            bar.get_width() + 5,
            bar.get_y() + bar.get_height() / 2,
            f"{val:,.1f}M",
            va="center",
            fontsize=9,
            color="#333333",
        )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlim(0, top15["Population (M)"].max() * 1.2)
    fig.text(
        0.99, 0.01,
        f"Source: REST Countries API  |  {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        ha="right", va="bottom", fontsize=8, color="grey",
    )
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[chart]     Saved → {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n=== Data Extraction Workflow ===\n")
    raw      = fetch_data()
    valid    = validate_response(raw)
    df       = transform_data(valid)
    save_csv(df)
    generate_summary(df)
    generate_chart(df)
    print("\n=== Workflow complete. Outputs saved to /output/ ===\n")


if __name__ == "__main__":
    main()
