# WeatherBot
# Автор: Сергей Сергиенко
# Год: 2025
# Telegram: @space_ranger3209
# Github: https://github.com/sergo100
# Все права защищены

import json
import requests
import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# 🔐 Токены
import os
from dotenv import load_dotenv
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ACCUWEATHER_TOKEN = os.getenv("ACCUWEATHER_TOKEN") # Переименовали переменную для токена AccuWeather
USER_DATA_FILE = 'user_data.json'

def load_user_data():
    """Загружает данные пользователей из файла."""
    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_user_data(data):
    """Сохраняет данные пользователей в файл."""
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f)

user_data = load_user_data()

# Словарь для сопоставления кодов иконок AccuWeather с эмодзи
weather_emojis = {
    1: "☀️", 2: "☀️", 3: "🌤️", 4: "🌤️", 5: "🌤️",
    6: "🌥️", 7: "☁️", 8: "☁️", 11: "🌫️",
    12: "🌧️", 13: "🌧️", 14: "🌧️", 15: "⛈️",
    16: "⛈️", 17: "⛈️", 18: "🌧️", 19: "🌨️",
    20: "🌨️", 21: "🌨️", 22: "❄️", 23: "❄️",
    24: "�", 25: "🌧️", 26: "🌧️", 29: "🌧️",
    30: "🥵", 31: "🥶", 32: "💨", 33: "🌙",
    34: "🌙", 35: "☁️", 36: "☁️", 37: "☁️",
    38: "☁️", 39: "🌧️", 40: "🌧️", 41: "⛈️",
    42: "⛈️", 43: "❄️", 44: "❄️"
}

def get_weather_emoji(icon_id):
    """Возвращает эмодзи погоды по коду иконки AccuWeather."""
    return weather_emojis.get(icon_id, '❔')

# Клавиатура
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        ["📍 Сменить город", "📅 Прогноз на 5 дней"],
        ["ℹ️ Об авторе", "💸 Помочь проекту"]
    ],
    resize_keyboard=True
)

# ------------------ ОБРАБОТЧИКИ ------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    await update.message.reply_text(
        "Привет! Я бот прогноза погоды.\nВыбери, что хочешь сделать:",
        reply_markup=main_menu
    )

async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений для установки города."""
    user_id = str(update.message.from_user.id)
    city = update.message.text.strip()

    # Проверяем на кнопки
    if city == "📍 Сменить город":
        await update.message.reply_text("Введите название нового города:")
        return
    elif city == "📅 Прогноз на 5 дней":
        await forecast(update, context)
        return
    elif city == "ℹ️ Об авторе":
        await about(update, context)
        return
    elif city == "💸 Помочь проекту":
        await donate(update, context)
        return

    location_key = validate_city(city)
    if location_key:
        user_data[user_id] = {"city_name": city, "location_key": location_key}
        save_user_data(user_data)
        await update.message.reply_text(f"Город сохранён: {city}")
    else:
        await update.message.reply_text("Не удалось найти такой город. Попробуй снова.")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QR_PATH = os.path.join(BASE_DIR, 'assets', 'donate_qr.png')

async def donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки помощи проекту."""
    try:
        if not os.path.exists(QR_PATH):
            await update.message.reply_text("QR-код для доната не найден. Свяжитесь с автором бота.")
            return

        with open(QR_PATH, 'rb') as qr:
            await update.message.reply_photo(
                photo=qr,
                caption="Спасибо за поддержку проекта! 💙\nОтсканируй QR-код СБП для перевода 🙏"
            )
    except Exception as e:
        await update.message.reply_text("Не удалось отправить QR-код 😢")
        print(f"Ошибка при отправке donate QR: {type(e).__name__}: {e}")

async def forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки прогноза на 5 дней."""
    user_id = str(update.message.from_user.id)
    user_info = user_data.get(user_id)
    if not user_info:
        await update.message.reply_text("Сначала укажи город. Нажми 📍 Сменить город")
        return

    city_name = user_info.get("city_name")
    location_key = user_info.get("location_key")
    text = get_forecast(city_name, location_key)
    await update.message.reply_text(text)

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Об авторе'."""
    await update.message.reply_text(
        "🤖 Бот прогноза погоды\n"
        "Автор: Сергей Сергиенко\n"
        "Telegram: @space_ranger3209\n"
        "Github: https://github.com/sergo100\n"
        "© 2025 Все права защищены"
    )

# ------------------ ПОГОДА ------------------

def validate_city(city):
    """
    Проверяет, существует ли город через API AccuWeather.
    Возвращает LocationKey, если город найден, иначе None.
    """
    try:
        url = f"http://dataservice.accuweather.com/locations/v1/cities/search?apikey={ACCUWEATHER_TOKEN}&q={city}&language=ru"
        print(f"Запрос к API: {url}") # Добавлено для отладки
        response = requests.get(url)
        data = response.json()
        
        # Добавлено для отладки: выводим статус ответа и сам ответ
        print(f"Статус ответа: {response.status_code}")
        print(f"Тело ответа: {data}")
        
        if response.status_code == 200 and data:
            return data[0]['Key']
        elif response.status_code == 503:
            print("Ошибка API: Превышен лимит запросов.")
            return "API_LIMIT_EXCEEDED"
        return None
    except Exception as e:
        print(f"Ошибка при валидации города AccuWeather: {e}")
        return None

def get_weather(city_name, location_key):
    """Получает текущую погоду для города с AccuWeather."""
    if location_key == "API_LIMIT_EXCEEDED":
        return "К сожалению, лимит запросов к API погоды превышен. Пожалуйста, попробуйте позже."
    
    try:
        url = f"http://dataservice.accuweather.com/currentconditions/v1/{location_key}?apikey={ACCUWEATHER_TOKEN}&language=ru&details=false"
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200 and data:
            temperature = data[0]['Temperature']['Metric']['Value']
            description = data[0]['WeatherText']
            icon_id = data[0]['WeatherIcon']
            emoji = get_weather_emoji(icon_id)
            return f"Погода в {city_name}: {emoji} {description}, {temperature}°C"
        elif response.status_code == 503:
            return "К сожалению, лимит запросов к API погоды превышен. Пожалуйста, попробуйте позже."
        else:
            return f"Не удалось получить погоду. Проверь название города."
    except Exception as e:
        print(f"Ошибка при получении погоды AccuWeather: {e}")
        return f"Не удалось получить погоду. Проверь название города."

def get_forecast(city_name, location_key):
    """Получает прогноз на 5 дней с AccuWeather."""
    if location_key == "API_LIMIT_EXCEEDED":
        return "К сожалению, лимит запросов к API погоды превышен. Пожалуйста, попробуйте позже."
    
    try:
        url = f"http://dataservice.accuweather.com/forecasts/v1/daily/5day/{location_key}?apikey={ACCUWEATHER_TOKEN}&language=ru&details=false&metric=true"
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200 and data and data.get('DailyForecasts'):
            result = f"Прогноз погоды в {city_name} (5 дней):\n"
            forecast_items = data['DailyForecasts'] # Берем все 5 дней

            for item in forecast_items:
                date = datetime.datetime.strptime(item['Date'], '%Y-%m-%dT%H:%M:%S%z').date()
                temperature_max = item['Temperature']['Maximum']['Value']
                temperature_min = item['Temperature']['Minimum']['Value']
                description = item['Day']['IconPhrase']
                icon_id = item['Day']['Icon']
                emoji = get_weather_emoji(icon_id)

                result += f"{date}: {emoji} {description}, от {temperature_min}°C до {temperature_max}°C\n"
            
            return result
        elif response.status_code == 503:
            return "К сожалению, лимит запросов к API погоды превышен. Пожалуйста, попробуйте позже."
        else:
            return "Ошибка при получении прогноза. Проверь название города."
    except Exception as e:
        print(f"Ошибка при получении прогноза AccuWeather: {e}")
        return "Ошибка при получении прогноза. Проверь название города."

# ------------------ РАСПИСАНИЕ И РАССЫЛКИ ------------------

async def send_daily_weather(context: ContextTypes.DEFAULT_TYPE):
    """Задача для ежедневной рассылки погоды."""
    for user_id, user_info in user_data.items():
        city_name = user_info.get("city_name")
        location_key = user_info.get("location_key")
        
        # Обновлено, чтобы использовать новую логику обработки ошибок
        if location_key == "API_LIMIT_EXCEEDED":
            text = "К сожалению, лимит запросов к API погоды превышен. Пожалуйста, попробуйте позже."
        else:
            text = get_weather(city_name, location_key)
        
        text += "\n\n© 2025 Сергей Сергиенко"
        try:
            await context.bot.send_message(chat_id=int(user_id), text=text)
        except Exception as e:
            print(f"Ошибка при ежедневной отправке пользователю {user_id}: {e}")

async def send_update_notification(context: ContextTypes.DEFAULT_TYPE):
    """Задача для одноразовой рассылки при запуске бота."""
    for user_id in user_data:
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text="🔄 Бот обновлён! Теперь более точная погода на 5 дней с пиктограммами.\nНажмите /start, и введите название вашего города занового, чтобы изменения вступили в силу."
            )
        except Exception as e:
            print(f"Ошибка при отправке обновления пользователю {user_id}: {e}")

# ------------------ ЗАПУСК ------------------

if __name__ == '__main__':
    # Создаем и настраиваем ApplicationBuilder
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_city))

    # Планируем задачи
    # Одноразовая рассылка обновления при запуске
    # `run_once` с задержкой 0 выполнит задачу сразу же после старта
    app.job_queue.run_once(send_update_notification, 0)
    
    # Ежедневная рассылка погоды в 8:00
    app.job_queue.run_daily(send_daily_weather, time=datetime.time(hour=8, minute=0))

    # Запускаем бота
    app.run_polling()
