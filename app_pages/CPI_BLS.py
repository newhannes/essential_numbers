######## ----------- CPI Inflation (BLS API) -------------- ########
import streamlit as st
import pandas as pd
import requests
import json
import pyperclip
import html2text
from datetime import datetime

st.write("Paste your BLS API key:")

BLS_API_KEY = st.text_input("BLS API Key")

SERIES_IDS = {
    "CUSR0000SA0":          "cpi_adjusted",
    "CUUR0000AA0":          "cpi_unadjusted",
    "CUSR0000SA0L1E":       "core_cpi_adjusted",
    "CUUR0000SA0L1E":       "core_cpi_unadjusted",
    "CUSR0000SA0E":         "energy_adjusted",
    "CUUR0000SA0E":         "energy_unadjusted",
    "CUSR0000SETB01":       "gas_adjusted",
    "CUUR0000SETB01":       "gas_unadjusted",
    "CUSR0000SAF11":        "food_at_home_adjusted",
    "CUUR0000SAF11":        "food_at_home_unadjusted",
    "CUSR0000SAH1":         "shelter_adjusted",
    "CUUR0000SAH1":         "shelter_unadjusted",
    "CUSR0000SEHA":         "rent_primary_residence_adjusted",
    "CUUR0000SEHA":         "rent_primary_residence_unadjusted",
    "CUSR0000SACL1E":       "core_commodities_adjusted",
    "CUUR0000SACL1E":       "core_commodities_unadjusted",
    "CUSR0000SA0L12E4":     "core_commodities_less_used_autos_adjusted",
    "CUUR0000SA0L12E4":     "core_commodities_less_used_autos_unadjusted",
}

# Display order and labels used in both report sections
DISPLAY_COLS = [
    ("cpi_yoy",                               "CPI (YoY)"),
    ("cpi_mom",                               "CPI (MoM)"),
    ("core_cpi_yoy",                          "Core CPI (YoY)"),
    ("core_cpi_mom",                          "Core CPI (MoM)"),
    ("food_at_home_yoy",                      "Food at Home (YoY)"),
    ("food_at_home_mom",                      "Food at Home (MoM)"),
    ("energy_yoy",                            "Energy (YoY)"),
    ("energy_mom",                            "Energy (MoM)"),
    ("shelter_yoy",                           "Shelter (YoY)"),
    ("shelter_mom",                           "Shelter (MoM)"),
    ("rent_primary_residence_yoy",            "Rent, Primary Residence (YoY)"),
    ("rent_primary_residence_mom",            "Rent, Primary Residence (MoM)"),
    ("gas_yoy",                               "Gasoline (YoY)"),
    ("gas_mom",                               "Gasoline (MoM)"),
    ("core_commodities_yoy",                  "Core Commodities (YoY)"),
    ("core_commodities_mom",                  "Core Commodities (MoM)"),
    ("core_commodities_less_used_autos_yoy",  "Core Commodities ex. Used Autos (YoY)"),
    ("core_commodities_less_used_autos_mom",  "Core Commodities ex. Used Autos (MoM)"),
]

# Administration comparison constants
TRUMP47_START       = "February 2025"
TRUMP_ENERGY_START  = "January 2025"
BIDEN_ENERGY_START  = "January 2021"


# ── Data helpers ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600 * 6)
def fetch_bls_cpi(start_year=2016, api_key=None):
    """Fetch CPI series from BLS API in small batches.

    The BLS API silently truncates responses when too many series are requested
    at once, causing the most-recent months to be dropped. Batching to 5 series
    per request avoids this.
    """
    end_year    = datetime.now().year
    series_list = list(SERIES_IDS.keys())
    batch_size  = 5
    batches     = [series_list[i:i + batch_size] for i in range(0, len(series_list), batch_size)]

    records = []
    for batch in batches:
        payload = {
            "seriesid":        batch,
            "startyear":       start_year,
            "endyear":         end_year,
            "catalog":         False,
            "registrationkey": api_key,
        }
        resp   = requests.post(
            "https://api.bls.gov/publicAPI/v2/timeseries/data/",
            data=json.dumps(payload),
            headers={"Content-type": "application/json"},
        )
        result = resp.json()
        if result["status"] != "REQUEST_SUCCEEDED":
            return None, result.get("message", ["Unknown BLS API error"])

        for series in result["Results"]["series"]:
            sid = series["seriesID"]
            for item in series["data"]:
                if "M01" <= item["period"] <= "M12":
                    records.append({
                        "series_id": sid,
                        "year":      item["year"],
                        "period":    item["period"],
                        "value":     item["value"],
                    })

    return pd.DataFrame(records), None


def process_cpi(raw_df):
    df = raw_df.assign(
        value=lambda x: pd.to_numeric(x["value"], errors="coerce"),
        series_name=lambda x: x["series_id"].map(SERIES_IDS),
        date=lambda x: pd.to_datetime(x["year"] + x["period"], format="%YM%m"),
    )
    cpi_raw = (
        df
        .pivot_table(index="date", columns="series_name", values="value", aggfunc="first")
        .sort_index()
        .reset_index()
        .assign(month_year=lambda x: x["date"].dt.strftime("%B %Y"))
        .set_index("month_year")
    )

    cpi = cpi_raw.copy()
    for col in list(cpi.columns):
        if col == "date":
            continue
        if "_unadjusted" in col:
            cpi[col.replace("unadjusted", "yoy")] = round(
                cpi[col].pct_change(periods=12, fill_method=None) * 100, 1
            )
        if "_adjusted" in col:
            cpi[col.replace("adjusted", "mom")] = round(
                cpi[col].pct_change(periods=1, fill_method=None) * 100, 1
            )

    rate_cols = [c for c in cpi.columns if "_yoy" in c or "_mom" in c]
    return cpi_raw, cpi[rate_cols]


# ── Load ───────────────────────────────────────────────────────────────────────

with st.spinner("Fetching CPI data from BLS..."):
    raw_df, error = fetch_bls_cpi(api_key=BLS_API_KEY)

if error:
    st.error(f"BLS API error: {error}")
    st.stop()

cpi_raw, cpi = process_cpi(raw_df)

# ── Title ──────────────────────────────────────────────────────────────────────

st.markdown("<h1 style='text-align: center;'>CPI Inflation</h1>", unsafe_allow_html=True)
st.caption(f"Most recent data: **{cpi.index[-1]}** · Source: U.S. Bureau of Labor Statistics")

# ── Top snapshot metrics ───────────────────────────────────────────────────────

snap = [
    ("cpi_yoy",      "CPI YoY"),
    ("core_cpi_yoy", "Core CPI YoY"),
    ("cpi_mom",      "CPI MoM"),
    ("core_cpi_mom", "Core CPI MoM"),
]
cols = st.columns(4)
for i, (col_name, label) in enumerate(snap):
    s = cpi[col_name].dropna()
    with cols[i]:
        st.metric(label, f"{s.iloc[-1]}%", delta=round(s.iloc[-1] - s.iloc[-2], 2))

st.markdown("---")

# ── Administration callouts ────────────────────────────────────────────────────

if TRUMP47_START in cpi.index:
    st.markdown("### Administration Stats (Feb. 2025 – Present)")
    trump47 = cpi.loc[TRUMP47_START:]

    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Avg. CPI (YoY)",
            f"{round(trump47['cpi_yoy'].mean(), 1)}%",
            help="Mean year-over-year CPI since February 2025",
        )
    with col2:
        st.metric(
            "Avg. Core CPI (YoY)",
            f"{round(trump47['core_cpi_yoy'].mean(), 1)}%",
            help="Mean year-over-year Core CPI since February 2025",
        )

    # Months with energy price declines
    if "energy_mom" in trump47.columns and "energy_yoy" in trump47.columns:
        mom_dec = int((trump47["energy_mom"] < 0).sum())
        yoy_dec = int((trump47["energy_yoy"] < 0).sum())
        total   = len(trump47)
        st.markdown(
            f"- **{mom_dec}/{total}** months since Feb. 2025 had month-over-month energy price **declines**."
        )
        st.markdown(
            f"- **{yoy_dec}/{total}** months had year-over-year energy price **declines**."
        )

    # Energy level change: Trump window vs. equivalent Biden window
    if (
        TRUMP_ENERGY_START in cpi_raw.index
        and BIDEN_ENERGY_START in cpi_raw.index
        and "energy_adjusted" in cpi_raw.columns
    ):
        t_start_val = cpi_raw.loc[TRUMP_ENERGY_START, "energy_adjusted"]
        t_end_val   = cpi_raw.iloc[-1]["energy_adjusted"]
        t_change    = round((t_end_val - t_start_val) / t_start_val * 100, 1)

        end_month, end_year = cpi_raw.index[-1].split()
        biden_equiv_end = f"{end_month} {int(end_year) - 4}"

        if biden_equiv_end in cpi_raw.index:
            b_start_val = cpi_raw.loc[BIDEN_ENERGY_START, "energy_adjusted"]
            b_end_val   = cpi_raw.loc[biden_equiv_end, "energy_adjusted"]
            b_change    = round((b_end_val - b_start_val) / b_start_val * 100, 1)
            st.markdown(
                f"- Energy prices changed **{t_change:+.1f}%** since January 2025 vs. "
                f"**{b_change:+.1f}%** during the equivalent Biden-era window "
                f"(Jan. 2021 – {biden_equiv_end})."
            )

    st.markdown("---")

# ── Dynamic Report ─────────────────────────────────────────────────────────────

if st.checkbox("Dynamic Report"):
    for col_name, label in DISPLAY_COLS:
        if col_name not in cpi.columns:
            continue
        s = cpi[col_name].dropna()
        if len(s) < 2:
            continue
        current, previous = s.iloc[-1], s.iloc[-2]
        avg_year = s.index[0].split()[1]

        st.markdown(f"## {label}")
        m_cols = st.columns(3)
        with m_cols[0]:
            st.metric(s.index[-1], f"{current}%", delta=round(current - previous, 2))
        with m_cols[1]:
            st.metric(s.index[-2], f"{previous}%")
        with m_cols[2]:
            st.metric(f"Avg. Since {avg_year}", f"{round(s.mean(), 1)}%")
        st.line_chart(s.iloc[-24:])

# ── Static Report ──────────────────────────────────────────────────────────────

if st.checkbox("Static Report"):
    final_report = ""
    for col_name, label in DISPLAY_COLS:
        if col_name not in cpi.columns:
            continue
        s = cpi[col_name].dropna()
        if len(s) < 2:
            continue
        current, previous = s.iloc[-1], s.iloc[-2]
        past     = s.iloc[:-1]
        avg_year = s.index[0].split()[1]

        higher_idx = past[past > current].last_valid_index()
        lower_idx  = past[past < current].last_valid_index()

        highest = (
            "This is the highest value on record."
            if pd.isna(higher_idx)
            else f"Last higher: {higher_idx} ({round(s.loc[higher_idx], 1)}%)"
        )
        lowest = (
            "This is the lowest value on record."
            if pd.isna(lower_idx)
            else f"Last lower: {lower_idx} ({round(s.loc[lower_idx], 1)}%)"
        )

        final_report += f"""
        <h3 style='margin-bottom:0px;'>{label}</h3>
        <ul style='margin-top:-17px;'>
            <li><b>{s.index[-1]}:</b> {current}%</li>
            <li><b>Previous ({s.index[-2]}):</b> {previous}%</li>
            <li><b>Context:</b>
                <ul>
                <li>{highest}</li>
                <li>{lowest}</li>
                <li>Average since {avg_year}: {round(s.mean(), 1)}%</li>
                </ul>
            </li>
        </ul>
        """

    if st.button("Copy to clipboard"):
        text_maker = html2text.HTML2Text()
        text_maker.ignore_links = True
        plain_text = text_maker.handle(final_report)
        plain_text = plain_text.replace("**", "").replace("###", "").replace("*", "-")
        pyperclip.copy(plain_text)
        st.success("Copied to clipboard!")

    st.markdown(final_report, unsafe_allow_html=True)

# ── Raw Data ───────────────────────────────────────────────────────────────────

if st.checkbox("Show Raw Data"):
    st.dataframe(cpi.tail(24))
