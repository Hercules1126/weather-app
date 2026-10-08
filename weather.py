"""OpenWeather requests and forecast formatting, separate from the screen."""
from datetime import datetime, timedelta, timezone
import requests

class WeatherError(Exception):
    """A safe message that can be displayed without exposing the API key."""


def fetch(path, key, **params):
    try:
        response = requests.get('https://api.openweathermap.org/' + path,
                                params={**params, 'appid': key}, timeout=15)
    except requests.RequestException:
        raise WeatherError('Cannot reach OpenWeather. Check your connection and try again.') from None
    if response.status_code == 401:
        raise WeatherError('OpenWeather rejected the API key. Check that it is correct and activated.')
    if response.status_code == 429:
        raise WeatherError('OpenWeather request limit reached. Please try again later.')
    if response.status_code != 200:
        raise WeatherError('OpenWeather is unavailable for this request. Please try again later.')
    try:
        return response.json()
    except ValueError:
        raise WeatherError('OpenWeather returned an unreadable response. Please try again later.') from None


def find_cities(query, key):
    cities = fetch('geo/1.0/direct', key, q=query.strip(), limit=5)
    if not isinstance(cities, list):
        raise WeatherError('Unexpected city search response. Try again later.')
    return cities


def city_label(city):
    return ', '.join(str(city[k]) for k in ('name', 'state', 'country') if city.get(k))


def local_time(timestamp, offset):
    return datetime.fromtimestamp(timestamp, timezone(timedelta(seconds=offset)))


def forecast_rows(data):
    offset = data['city']['timezone']
    return [{
        'Local time': local_time(item['dt'], offset).strftime('%Y-%m-%d %H:%M'),
        'Temperature (°C)': round(item['main']['temp'], 1),
        'Feels like (°C)': round(item['main']['feels_like'], 1),
        'Rain chance (%)': round(item.get('pop', 0) * 100),
        'Conditions': item['weather'][0]['description'].capitalize(),
    } for item in data['list']]
