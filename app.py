"""Run with: python -m streamlit run app.py"""
import os
import pandas as pd
import streamlit as st
from weather import WeatherError, fetch, find_cities, city_label, local_time, forecast_rows

st.set_page_config(page_title='Hercules Weather', page_icon='🌤️', layout='centered')
st.title('🌤️ Hercules Weather')
st.write('A little forecast for your next adventure.')
st.caption('Search a city, check the weather, and plan your day.')

# The key stays on the server; never paste it into the Python source.
key = os.environ.get('OPENWEATHER_API_KEY', '')
if not key:
    try:
        key = st.secrets.get('OPENWEATHER_API_KEY', '')
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        key = ''
if not key or key == 'PASTE_YOUR_KEY_HERE':
    st.info('Setup needed: add OPENWEATHER_API_KEY to Streamlit Secrets. See README.md for the steps.')
    st.stop()

# Cache repeated requests for ten minutes to reduce API usage.
@st.cache_data(ttl=600, max_entries=256, show_spinner=False)
def search(query, api_key):
    return find_cities(query, api_key)

@st.cache_data(ttl=600, max_entries=256, show_spinner=False)
def conditions(lat, lon, api_key):
    return fetch('data/2.5/weather', api_key, lat=lat, lon=lon, units='metric')

@st.cache_data(ttl=600, max_entries=256, show_spinner=False)
def outlook(lat, lon, api_key):
    return fetch('data/2.5/forecast', api_key, lat=lat, lon=lon, units='metric')

# Pasig and Manila are separate cities in Metro Manila.
with st.form('city_search'):
    query = st.text_input('City name', placeholder='Try Cebu, PH or Tokyo, JP', max_chars=100)
    submitted = st.form_submit_button('Search city', type='primary')

left, right = st.columns(2)
if left.button('📍 Pasig City', width='stretch'):
    st.session_state['query'] = 'Pasig,PH'
if right.button('📍 Manila', width='stretch'):
    st.session_state['query'] = 'Manila,PH'
if submitted:
    if query.strip():
        st.session_state['query'] = query.strip()
    else:
        st.warning('Please enter a city name.')
        st.stop()
if 'query' not in st.session_state:
    st.session_state['query'] = 'Pasig,PH'

try:
    with st.spinner('Finding your city…'):
        matches = search(st.session_state['query'], key)
    if not matches:
        st.warning('No city found. Check the spelling or add a country code, such as Pasig, PH.')
        st.stop()
    # Let the user choose when different places have the same name.
    selected = st.selectbox('Matching location', range(len(matches)),
                            format_func=lambda i: city_label(matches[i]),
                            key='location_' + st.session_state['query'])
    city = matches[selected]
    st.subheader(city_label(city))
    st.caption(f"Coordinates: {city['lat']:.4f}, {city['lon']:.4f}")
    with st.spinner('Checking current weather…'):
        current = conditions(city['lat'], city['lon'], key)
    st.write(current['weather'][0]['description'].capitalize())
    a, b, c = st.columns(3)
    a.metric('Temperature', f"{current['main']['temp']:.1f} °C")
    b.metric('Feels like', f"{current['main']['feels_like']:.1f} °C")
    c.metric('Humidity', f"{current['main']['humidity']}%")
    st.caption(f"Wind: {current['wind']['speed'] * 3.6:.1f} km/h · "
               f"Observation: {local_time(current['dt'], current['timezone']).strftime('%d %b %Y, %I:%M %p %z')}")

    st.subheader('5-day forecast')
    st.caption('Forecast every 3 hours. Times are local to the selected city. Data is cached for up to 10 minutes.')
    with st.spinner('Loading the forecast…'):
        forecast = outlook(city['lat'], city['lon'], key)
    rows = forecast_rows(forecast)
    if not rows:
        st.info('No forecast entries are available right now.')
    else:
        frame = pd.DataFrame(rows)
        st.line_chart(frame.set_index('Local time')[['Temperature (°C)']])
        st.dataframe(frame, hide_index=True, width='stretch')
except WeatherError as error:
    st.error(str(error))
except (KeyError, TypeError, IndexError, ValueError):
    st.error('Some weather details are missing. Please try again later.')

st.divider()
st.markdown('Weather data by [OpenWeather](https://openweathermap.org/) · Built with Streamlit')
