from generate_csv import *
from analysis import *
import requests
import streamlit as st
import pandas as pd
from datetime import datetime, timezone
import aiohttp
import plotly.express as px
import plotly.graph_objects as go
# import asyncio

URL = "https://api.openweathermap.org/data/2.5/weather"

st.set_page_config("Анализ данных о погоде", page_icon="☀️")

def fetch_current_weather(city, api_key):
    params = {"q": city, "APPID": api_key}
    response = requests.get(URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Ошибка при получении данных о погоде: {response.json()['message']}")
        return []

async def fetch_current_weather_async(city, api_key):
    params = {"q": city, "APPID": api_key}
    async with aiohttp.ClientSession() as session:
        async with session.get(URL, params=params) as response:
            data = await response.json()
            if response.status == 200:
                return data
            else:
                st.error(f"Ошибка при получении данных о погоде: {data['message']}")
                return []

def get_season_from_api_response(resp):
    dt_utc = resp["dt"]
    tz_shift = resp.get("timezone", 0)

    local_dt = datetime.fromtimestamp(dt_utc + tz_shift, tz=timezone.utc)
    month = local_dt.month

    if month in (12, 1, 2):
        return "winter"
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    return "autumn"


st.markdown("# Анализ погоды")

st.markdown("### Исторические данные и анализ")
file = st.file_uploader("Загрузите csv файл с историческими данными о погоде", type="csv")
if file is None:
    st.info("Загрузите CSV файл для начала работы")
else:
    df = pd.read_csv(file)
    st.markdown("### Загруженный датасет")
    st.dataframe(df)
    st.markdown("### Датасет после анализа")
    st.markdown("- Посчитано скользящее среднее с окном в 30 дней\n- Рассчитана средняя температура и стандартное отклонение для каждого сезона в каждом городе.\n- Выявлены аномалии")
    analysis_data = analysis_pipeline(df)
    st.dataframe(analysis_data)
    st.markdown("### Текущая погода")

    api_key = st.text_input("Введите API ключ")
    city = st.selectbox("Выберите город для загрузки текущей погоды", seasonal_temperatures.keys())
    city_df = analysis_data[analysis_data["city"] == city].copy()
    city_df = city_df.sort_values("timestamp")

    if st.button("Загрузить текущую погоду"):
        # Получение текущей погоды через async
        # data = asyncio.run(fetch_current_weather_async(city, api_key))
        data = fetch_current_weather(city, api_key)

        if data:
            temp = data['main']['temp'] - 273.15
            st.write(f"Текущая температура в {city} - {temp:.4f}°C")
            season = get_season_from_api_response(data)
            if is_anomalies(analysis_data, temp, season, city):
                st.warning("Аномальная температура!")
            else:
                st.success("Температура в пределах нормы!")

    if st.checkbox("Показать описательную статистику для загруженных данных"):
        st.markdown(f"#### Ключевые метрики для {city}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Минимальная температура (°C)", f"{city_df['temperature'].min():.2f}")
            st.metric("Максимальная температура (°C)", f"{city_df['temperature'].max():.2f}")
        with col2:
            st.metric("Средняя температура (°C)", f"{city_df['temperature'].mean():.2f}")
            st.metric("Медиана (°C)", f"{city_df['temperature'].median():.2f}")
        with col3:
            st.metric("Стандартное отклонение (°C)", f"{city_df['temperature'].std():.2f}")
            st.metric("Процент аномалий", f"{city_df['is_anomaly'].mean():.2f}")

        st.markdown("### Описательная таблица")
        st.write(city_df.describe(include="all"))

        fig = px.box(
            city_df,
            x="season",
            y="temperature",
            category_orders={"season": ["winter", "spring", "summer", "autumn"]},
            title="Распределение температур по сезонам"
        )
        st.plotly_chart(fig, use_container_width=True)

    if st.checkbox("Временной ряд температур с выделением аномалий"):
        anom_df = city_df[city_df["is_anomaly"] == True]
        st.markdown(f"### Временной ряд температур и аномалии для {city}")

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=city_df["timestamp"],
            y=city_df["temperature"],
            mode="lines",
            name="Температура"
        ))

        fig.add_trace(go.Scatter(
            x=anom_df["timestamp"],
            y=anom_df["temperature"],
            mode="markers",
            name="Аномалии"
        ))

        fig.update_layout(
            xaxis_title="Дата",
            yaxis_title="Температура (°C)",
        )

        st.plotly_chart(fig, use_container_width=True)

    if st.checkbox("Сезонные профили"):
        st.markdown(f"### Сезонные профили для {city}")
        season_profile = (city_df[["season", "mean", "std"]].drop_duplicates())

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=season_profile["season"],
            y=season_profile["mean"],
            name="Средняя температура",
            error_y=dict(
                type="data",
                array=season_profile["std"],
                visible=True
            )
        ))

        fig.update_layout(
            xaxis_title="Сезон",
            yaxis_title="Температура (°C)",
        )

        st.plotly_chart(fig, use_container_width=True)
