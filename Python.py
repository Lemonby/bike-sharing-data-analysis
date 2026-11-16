from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "Bike-sharing-dataset"

SEASON_LABELS = {
    1: "Spring",
    2: "Summer",
    3: "Fall",
    4: "Winter",
}

WEATHER_LABELS = {
    1: "Clear",
    2: "Mist/Cloudy",
    3: "Light Rain/Snow",
    4: "Heavy Rain/Snow",
}

DAY_TYPE_LABELS = {
    0: "Non-workingday",
    1: "Workingday",
}


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    day_df = pd.read_csv(DATA_DIR / "day.csv", parse_dates=["dteday"])
    hour_df = pd.read_csv(DATA_DIR / "hour.csv", parse_dates=["dteday"])

    for data in (day_df, hour_df):
        data["year"] = data["yr"].map({0: 2011, 1: 2012})
        data["season_label"] = data["season"].map(SEASON_LABELS)
        data["weather_label"] = data["weathersit"].map(WEATHER_LABELS)
        data["day_type"] = data["workingday"].map(DAY_TYPE_LABELS)

    return day_df, hour_df


def format_number(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


st.set_page_config(
    page_title="Bike Sharing Dashboard",
    page_icon="🚲",
    layout="wide",
)

st.title("Bike Sharing Dashboard")
st.markdown(
    "Dashboard interaktif untuk menganalisis pola penyewaan sepeda berdasarkan "
    "waktu, jenis hari, musim, dan kondisi cuaca selama 2011–2012."
)

day_df, hour_df = load_data()

st.sidebar.header("Filter")
selected_years = st.sidebar.multiselect(
    "Tahun",
    options=sorted(day_df["year"].unique()),
    default=sorted(day_df["year"].unique()),
)
selected_day_types = st.sidebar.multiselect(
    "Jenis hari",
    options=list(DAY_TYPE_LABELS.values()),
    default=list(DAY_TYPE_LABELS.values()),
)

filtered_day = day_df[day_df["year"].isin(selected_years)].copy()
filtered_hour = hour_df[
    hour_df["year"].isin(selected_years)
    & hour_df["day_type"].isin(selected_day_types)
].copy()

if filtered_day.empty or filtered_hour.empty:
    st.warning("Tidak ada data untuk kombinasi filter yang dipilih.")
    st.stop()

total_rentals = filtered_day["cnt"].sum()
average_daily = filtered_day["cnt"].mean()
peak_hour_row = (
    filtered_hour.groupby("hr", as_index=False)["cnt"]
    .mean()
    .sort_values("cnt", ascending=False)
    .iloc[0]
)

metric_1, metric_2, metric_3 = st.columns(3)
metric_1.metric("Total penyewaan", format_number(total_rentals))
metric_2.metric("Rata-rata penyewaan harian", format_number(average_daily))
metric_3.metric(
    "Jam dengan rata-rata tertinggi",
    f"{int(peak_hour_row['hr']):02d}.00",
)

st.subheader("Pola Penyewaan Berdasarkan Jam")
hourly_rentals = (
    filtered_hour.groupby(["day_type", "hr"], as_index=False)["cnt"]
    .mean()
    .rename(columns={"cnt": "avg_rentals"})
)

fig_hour, ax_hour = plt.subplots(figsize=(12, 5))
for day_type, group in hourly_rentals.groupby("day_type"):
    ax_hour.plot(
        group["hr"],
        group["avg_rentals"],
        marker="o",
        linewidth=2,
        label=day_type,
    )
ax_hour.set_title("Rata-rata Penyewaan per Jam dan Jenis Hari")
ax_hour.set_xlabel("Jam")
ax_hour.set_ylabel("Rata-rata Penyewaan")
ax_hour.set_xticks(range(24))
ax_hour.grid(alpha=0.25)
ax_hour.legend(title="Jenis Hari")
fig_hour.tight_layout()
st.pyplot(fig_hour)
plt.close(fig_hour)

st.subheader("Penyewaan Berdasarkan Musim dan Cuaca")
seasonal_rentals = (
    filtered_day.groupby("season_label", as_index=False)["cnt"]
    .mean()
    .rename(columns={"cnt": "avg_rentals"})
)
seasonal_rentals["season_label"] = pd.Categorical(
    seasonal_rentals["season_label"],
    categories=["Spring", "Summer", "Fall", "Winter"],
    ordered=True,
)
seasonal_rentals = seasonal_rentals.sort_values("season_label")

weather_rentals = (
    filtered_day.groupby("weather_label", as_index=False)["cnt"]
    .mean()
    .rename(columns={"cnt": "avg_rentals"})
)

chart_1, chart_2 = st.columns(2)
with chart_1:
    st.caption("Rata-rata penyewaan harian berdasarkan musim")
    st.bar_chart(
        seasonal_rentals.set_index("season_label")["avg_rentals"],
        y_label="Rata-rata Penyewaan",
    )

with chart_2:
    st.caption("Rata-rata penyewaan harian berdasarkan kondisi cuaca")
    st.bar_chart(
        weather_rentals.set_index("weather_label")["avg_rentals"],
        y_label="Rata-rata Penyewaan",
    )

st.subheader("Ringkasan Temuan")
best_season = seasonal_rentals.loc[
    seasonal_rentals["avg_rentals"].idxmax(), "season_label"
]
best_weather = weather_rentals.loc[
    weather_rentals["avg_rentals"].idxmax(), "weather_label"
]
st.markdown(
    f"- Musim dengan rata-rata penyewaan tertinggi pada filter saat ini adalah "
    f"**{best_season}**.\n"
    f"- Kondisi cuaca dengan rata-rata penyewaan tertinggi adalah "
    f"**{best_weather}**.\n"
    "- Ketersediaan sepeda sebaiknya diprioritaskan pada jam permintaan tinggi "
    "dan disesuaikan dengan kondisi musim serta cuaca."
)
