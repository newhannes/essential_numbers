# -------------------------------------------------------------------------
# Interactive explorer of CBO's real GDP growth projections vs. actuals.
#
# Cycle through each CBO economic-projection vintage and compare its
# projected real GDP growth path to what GDP actually did (BEA, annual).
# KPIs show CBO's average projected growth over the forecast window and
# what GDP actually averaged over the same (available-actual) years.
# -------------------------------------------------------------------------

import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

# House Budget Committee colors (kept local so this page has no dependency
# on the parent HELPERS package, which is outside this deployed repo).
JADE = "#84AE95"
EMERALD = "#004647"
GOLD = "#967D4A"
RUST = "#C85D5D"
LIGHT_GREY = "#C5C6C7"

MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11,
    "December": 12,
}

st.title("CBO Real GDP Projection Explorer")
st.write(
    "Cycle through each of CBO's economic-projection vintages and compare its "
    "projected **real GDP growth** path to what GDP actually did. "
    "Projections are CBO's; actuals are from BEA (NIPA Table 1.1.1, annual)."
)


# -------------------------------------------------------------------------
# Data loading
# -------------------------------------------------------------------------
@st.cache_data(ttl=60 * 60 * 24)
def load_projections() -> pd.DataFrame:
    """CBO real GDP projections (one row per vintage x projected year)."""
    df = pd.read_csv("data/real_gdp_projections.csv")
    parts = df["projection_date"].str.split(" ", n=1, expand=True)
    df["pub_year"] = parts[0].astype(int)
    df["pub_month"] = parts[1].map(MONTHS).fillna(1).astype(int)
    return df


@st.cache_data(ttl=60 * 60 * 6, show_spinner="Fetching actual GDP from BEA...")
def fetch_actual_growth() -> pd.DataFrame:
    """Actual annual real GDP growth (%) from BEA NIPA Table 1.1.1."""
    api_key = st.secrets["BEA_API_KEY"]
    url = (
        "https://apps.bea.gov/api/data/?&UserID=" + api_key +
        "&method=GetData&DataSetName=NIPA&TableName=T10101"
        "&Frequency=A&Year=X&ResultFormat=json"
    )
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    rows = resp.json()["BEAAPI"]["Results"]["Data"]
    actual = pd.DataFrame(rows)
    actual = actual[actual["LineDescription"] == "Gross domestic product"].copy()
    actual["year"] = actual["TimePeriod"].astype(int)
    actual["actual_growth"] = pd.to_numeric(
        actual["DataValue"].astype(str).str.replace(",", "", regex=False),
        errors="coerce",
    )
    return actual[["year", "actual_growth"]].dropna().sort_values("year").reset_index(drop=True)


cbo = load_projections()

try:
    actual = fetch_actual_growth()
except Exception as exc:  # noqa: BLE001 - surface any BEA/secret issue in-app
    st.error(
        "Could not fetch actual GDP from BEA. Check that `BEA_API_KEY` is set in "
        f"Streamlit secrets.\n\nDetails: {exc}"
    )
    st.stop()

actual_by_year = dict(zip(actual["year"], actual["actual_growth"]))


# -------------------------------------------------------------------------
# Vintage selector (chronological) with prev / next cycling
# -------------------------------------------------------------------------
vintage_order = (
    cbo[["projection_date", "pub_year", "pub_month"]]
    .drop_duplicates()
    .sort_values(["pub_year", "pub_month"])
)
vintages = vintage_order["projection_date"].tolist()

# The selectbox's own widget state ("cbo_gdp_select") is the single source of
# truth. Default to the most recent vintage.
if "cbo_gdp_select" not in st.session_state or st.session_state.cbo_gdp_select not in vintages:
    st.session_state.cbo_gdp_select = vintages[-1]

current_idx = vintages.index(st.session_state.cbo_gdp_select)

prev_col, sel_col, next_col = st.columns([1, 4, 1])

# Process the buttons BEFORE creating the selectbox so the new value is picked
# up by the widget on this same rerun.
with prev_col:
    st.write("")
    if st.button("◀ Prev", use_container_width=True, disabled=current_idx == 0):
        st.session_state.cbo_gdp_select = vintages[current_idx - 1]

with next_col:
    st.write("")
    if st.button("Next ▶", use_container_width=True, disabled=current_idx == len(vintages) - 1):
        st.session_state.cbo_gdp_select = vintages[current_idx + 1]

with sel_col:
    vintage = st.selectbox(
        "CBO projection vintage",
        vintages,
        key="cbo_gdp_select",
    )


# -------------------------------------------------------------------------
# Build the selected vintage's forecast series
# -------------------------------------------------------------------------
sub = cbo[cbo["projection_date"] == vintage].sort_values("year")
pub_year = int(sub["pub_year"].iloc[0])

# "Forecast years" = the publication year and beyond (drops the prior-year
# historical anchor CBO includes as projection_year 1).
forecast = sub[sub["year"] >= pub_year].copy()
forecast["actual_growth"] = forecast["year"].map(actual_by_year)

forecast_start, forecast_end = int(forecast["year"].min()), int(forecast["year"].max())

# Overlap = forecast years for which an actual exists (apples-to-apples window).
overlap = forecast.dropna(subset=["actual_growth"])
has_overlap = not overlap.empty


# -------------------------------------------------------------------------
# KPIs: average projected vs. average actual growth over the window
# -------------------------------------------------------------------------
st.subheader(f"{vintage} projection")

if has_overlap:
    ov_start, ov_end = int(overlap["year"].min()), int(overlap["year"].max())
    cbo_avg = overlap["real_gdp_pct_change"].mean()
    actual_avg = overlap["actual_growth"].mean()
    miss = actual_avg - cbo_avg
    span_label = f"{ov_start}–{ov_end}" if ov_start != ov_end else f"{ov_start}"
    n_years = overlap["year"].nunique()

    k1, k2, k3 = st.columns(3)
    k1.metric("CBO avg projected growth", f"{cbo_avg:.2f}%")
    k2.metric("Actual avg growth", f"{actual_avg:.2f}%")
    k3.metric(
        "Actual minus CBO",
        f"{miss:+.2f} pp",
        delta=f"{miss:+.2f} pp",
        delta_color="normal",
        help="Positive = CBO under-projected growth; negative = CBO over-projected.",
    )
    st.caption(
        f"Averages over forecast years **{span_label}** ({n_years} year"
        f"{'s' if n_years != 1 else ''} with available actuals). "
        f"Full CBO forecast window: {forecast_start}–{forecast_end}."
    )
else:
    cbo_avg_full = forecast["real_gdp_pct_change"].mean()
    k1, k2 = st.columns(2)
    k1.metric(
        f"CBO avg projected growth ({forecast_start}–{forecast_end})",
        f"{cbo_avg_full:.2f}%",
    )
    k2.metric("Actual avg growth", "n/a")
    st.caption(
        f"No actual GDP data is available yet for this forecast window "
        f"({forecast_start}–{forecast_end}), so no comparison is shown."
    )


# -------------------------------------------------------------------------
# Interactive chart
# -------------------------------------------------------------------------
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=forecast["year"],
        y=forecast["real_gdp_pct_change"],
        mode="lines+markers",
        name=f"CBO projection ({vintage})",
        line=dict(color=EMERALD, width=3),
        marker=dict(size=6),
        hovertemplate="%{x}: %{y:.2f}%<extra>CBO</extra>",
    )
)

if has_overlap:
    fig.add_trace(
        go.Scatter(
            x=overlap["year"],
            y=overlap["actual_growth"],
            mode="lines+markers",
            name="Actual real GDP growth",
            line=dict(color=GOLD, width=3),
            marker=dict(size=6),
            hovertemplate="%{x}: %{y:.2f}%<extra>Actual</extra>",
        )
    )

fig.add_hline(y=0, line_dash="dash", line_color=LIGHT_GREY)

fig.update_layout(
    title=dict(text="Real GDP Growth: CBO Projection vs. Actual", x=0.0, font=dict(size=18)),
    yaxis=dict(title="Real GDP growth", ticksuffix="%", zeroline=False),
    xaxis=dict(title="Year", dtick=1),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    hovermode="x unified",
    margin=dict(l=10, r=10, t=70, b=10),
    height=480,
    plot_bgcolor="white",
)
fig.update_xaxes(showgrid=False)
fig.update_yaxes(showgrid=True, gridcolor="#EEEEEE")

st.plotly_chart(fig, use_container_width=True)


# -------------------------------------------------------------------------
# Raw data (optional)
# -------------------------------------------------------------------------
with st.expander("View the data for this vintage"):
    show = forecast[["year", "real_gdp_pct_change", "actual_growth"]].rename(
        columns={
            "real_gdp_pct_change": "CBO projected growth (%)",
            "actual_growth": "Actual growth (%)",
        }
    )
    st.dataframe(show.set_index("year"), use_container_width=True)
