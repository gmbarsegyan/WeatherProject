import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go

cities = ['New York', 'London', 'Paris', 'Tokyo', 'Moscow', 'Sydney', 
        'Berlin', 'Beijing', 'Rio de Janeiro', 'Dubai', 'Los Angeles',
        'Singapore', 'Mumbai', 'Cairo', 'Mexico City']

month_to_season = {12: "winter", 1: "winter", 2: "winter",
                   3: "spring", 4: "spring", 5: "spring",
                   6: "summer", 7: "summer", 8: "summer",
                   9: "autumn", 10: "autumn", 11: "autumn"}

def rolling_mean(args):
    city, city_data = args

    city_data['rolling_mean'] = city_data['temperature'].rolling(window=30).mean()
    city_data['rolling_std'] = city_data['temperature'].rolling(window=30).std()
    city_data['is_outlier'] = (
        (city_data['temperature'] < city_data['rolling_mean'] - 2*city_data['rolling_std']) |
        (city_data['temperature'] > city_data['rolling_mean'] + 2*city_data['rolling_std'])
    )
    season_mean = city_data.groupby('season')['temperature'].mean()
    season_std = city_data.groupby('season')['temperature'].std()
    return (city, {
        'season_mean': season_mean, 
        'season_std': season_std, 
        'city_data': city_data
    })


st.title("Анализ температурных данных")
st.header("Ввод данных")
file = st.file_uploader("Загрузите файл с историческими данными", type=["csv", "xlsx"])
city = st.selectbox("Выберите город", cities)
api_key = st.text_input("Введите API-ключ OpenWeatherMap")

if file:
    data = pd.read_csv(file) if file.type == "text/csv" else pd.read_excel(file)

    if city:
        st.header("Исторические данные")
        city_data = data[data['city'] == city].copy()

        st.subheader("Описательная статистика")
        st.dataframe(city_data['temperature'].describe())

        city_data['rolling_mean'] = city_data['temperature'].rolling(window=30).mean()
        city_data['rolling_std'] = city_data['temperature'].rolling(window=30).std()
        city_data['upper_bound'] = city_data['rolling_mean'] + 2 * city_data['rolling_std']
        city_data['lower_bound'] = city_data['rolling_mean'] - 2 * city_data['rolling_std']
        city_data['is_outlier'] = (
            (city_data['temperature'] < city_data['lower_bound']) |
            (city_data['temperature'] > city_data['upper_bound'])
        )

        st.subheader("Исторический график температуры")
        fig = go.Figure()

        normal_data = city_data[~city_data['is_outlier']]
        fig.add_trace(go.Scatter(
            x=normal_data['timestamp'],
            y=normal_data['temperature'],
            mode='lines',
            name='Температура',
            line=dict(color='blue', width=1)))

        fig.add_trace(go.Scatter(
            x=city_data['timestamp'],
            y=city_data['rolling_mean'],
            mode='lines',
            name='Скользящее среднее (30 дней)',
            line=dict(color='green', width=2)))

        fig.add_trace(go.Scatter(
            x=city_data['timestamp'],
            y=city_data['upper_bound'],
            mode='lines',
            name='Верхняя граница',
            line=dict(color='orange', width=1, dash='dash')))

        fig.add_trace(go.Scatter(
            x=city_data['timestamp'],
            y=city_data['lower_bound'],
            mode='lines',
            name='Нижняя граница',
            line=dict(color='orange', width=1, dash='dash')))

        outliers = city_data[city_data['is_outlier']]
        fig.add_trace(go.Scatter(
            x=outliers['timestamp'],
            y=outliers['temperature'],
            mode='markers',
            name='Выбросы',
            marker=dict(color='red', size=6)))
        
        fig.update_layout(
            xaxis_title='Дата',
            yaxis_title='Температура (°C)')
        
        st.plotly_chart(fig, use_container_width=True)


if api_key is not None and city is not None and file is not None:
    st.header("Анализ текущей температуры")
    response = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric")
    if response.status_code == 200:
        weather_data = response.json()
        current_temperature = weather_data['main']['temp']
        st.write(f"Текущая температура в {city} равна {current_temperature}°C")

        current_season = month_to_season[datetime.now().month]
        _, city_stats = rolling_mean((city, city_data))
        normal_temperature_mean = city_stats['season_mean'][current_season]
        normal_temperature_std = city_stats['season_std'][current_season]

        if current_temperature < normal_temperature_mean - 2*normal_temperature_std or current_temperature > normal_temperature_mean + 2*normal_temperature_std:
            st.write("Температура аномальная, согласно историческим данным")
        else:
            st.write("Температура нормальная, согласно историческим данным")
    else:
        st.error(response.json())
    

























