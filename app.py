from flask import Flask, request, render_template
import requests

app = Flask(__name__)

BASE_URL = "http://dataservice.accuweather.com"
API_KEY = "WaQUzVDHxfpuBEXMpujfzVs6bnBYapxA"

def evaluate_weather_conditions(min_temp, max_temp, wind_speed, precipitation_chance):
    if min_temp < 0 or max_temp > 35:
        return "Температура экстремальна!"
    if wind_speed > 50:
        return "Сильный ветер!"
    if precipitation_chance > 70:
        return "Высокая вероятность осадков!"
    return "Погода благоприятная."

def fetch_location_key(latitude, longitude):
    url = f"{BASE_URL}/locations/v1/cities/geoposition/search?apikey={API_KEY}&q={latitude}%2C{longitude}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get('Key')
    except requests.RequestException as e:
        return None

def fetch_weather_info(location_key):
    url = f"{BASE_URL}/forecasts/v1/daily/1day/{location_key}?apikey={API_KEY}&language=en-us&details=true&metric=true"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return None

def validate_coordinates(lat, lon):
    try:
        lat = float(lat)
        lon = float(lon)
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return True
    except ValueError:
        pass
    return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/weather', methods=['POST'])
def get_weather():
    start_latitude = request.form['lat_st']
    start_longitude = request.form['lon_st']
    end_latitude = request.form['lat_end']
    end_longitude = request.form['lon_end']

    if not all([start_latitude, start_longitude, end_latitude, end_longitude]):
        return "Ошибка: Укажите все координаты!", 400

    if not (validate_coordinates(start_latitude, start_longitude) and
            validate_coordinates(end_latitude, end_longitude)):
        return "Ошибка: Введены некорректные координаты! Пожалуйста, убедитесь, что широта находится в диапазоне от -90 до 90 и долгота от -180 до 180.", 400

    start_location_key = fetch_location_key(start_latitude, start_longitude)
    if not start_location_key:
        return "Ошибка: Не удалось найти начальную точку! Проверьте введенные координаты.", 400

    end_location_key = fetch_location_key(end_latitude, end_longitude)
    if not end_location_key:
        return "Ошибка: Не удалось найти конечную точку! Проверьте введенные координаты.", 400

    start_weather_data = fetch_weather_info(start_location_key)
    end_weather_data = fetch_weather_info(end_location_key)

    if not start_weather_data or not end_weather_data:
        return "Ошибка: Не удалось получить данные о погоде! Попробуйте позже.", 400

    start_forecast = start_weather_data['DailyForecasts'][0]
    end_forecast = end_weather_data['DailyForecasts'][0]

    max_temp_start = start_forecast['Temperature']['Maximum']['Value']
    min_temp_start = start_forecast['Temperature']['Minimum']['Value']
    wind_speed_start = start_forecast['Day']['Wind']['Speed']['Value']
    rain_prob_start = start_forecast['Day']['PrecipitationProbability']

    max_temp_end = end_forecast['Temperature']['Maximum']['Value']
    min_temp_end = end_forecast['Temperature']['Minimum']['Value']
    wind_speed_end = end_forecast['Day']['Wind']['Speed']['Value']
    rain_prob_end = end_forecast['Day']['PrecipitationProbability']

    report_start = evaluate_weather_conditions(min_temp_start, max_temp_start, wind_speed_start, rain_prob_start)
    report_end = evaluate_weather_conditions(min_temp_end, max_temp_end, wind_speed_end, rain_prob_end)

    return f'''
            <h2>Прогноз для начальной точки:</h2>
            <p>{report_start}</p>
            <h2>Прогноз для конечной точки:</h2>
            <p>{report_end}</p>
            <a href="/">Назад</a>
        '''

if __name__ == '__main__':
    app.run(debug=True)
