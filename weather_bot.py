# WeatherBot
# Автор: Сергей Сергиенко
# Год: 2025
# Telegram: @space_ranger3209
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
WEATHERAPI_TOKEN = os.getenv("WEATHERAPI_TOKEN") 
USER_DATA_FILE = 'user_data.json'

def load_user_data():
    """Загружает данные пользователей из файла."""
    try:
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_user_data(data):
    """Сохраняет данные пользователей в файл."""
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

user_data = load_user_data()

# Словарь для сопоставления кодов иконок WeatherAPI.com с эмодзи
# Используем код погоды (code) и по возможности флаг дня/ночи (is_day) для большей точности
weather_emojis = {
    1000: {"day": "☀️", "night": "🌙"},
    1003: {"day": "🌤️", "night": "☁️"},
    1006: {"day": "☁️", "night": "☁️"},
    1009: {"day": "☁️", "night": "☁️"},
    1030: "🌫️",
    1063: "🌧️",
    1066: "❄️",
    1069: "🌧️",
    1072: "🌧️",
    1087: "⛈️",
    1114: "🌨️",
    1117: "🌨️",
    1135: "🌫️",
    1147: "🌫️",
    1150: "🌧️",
    1153: "🌧️",
    1168: "🌧️",
    1171: "🌧️",
    1180: "🌧️",
    1183: "🌧️",
    1186: "🌧️",
    1189: "🌧️",
    1192: "🌧️",
    1195: "🌧️",
    1198: "🌧️",
    1201: "🌧️",
    1204: "🌧️",
    1207: "🌧️",
    1210: "🌨️",
    1213: "🌨️",
    1216: "❄️",
    1219: "❄️",
    1222: "❄️",
    1225: "❄️",
    1237: "🌨️",
    1240: "🌧️",
    1243: "🌧️",
    1246: "🌧️",
    1249: "🌧️",
    1252: "🌧️",
    1255: "❄️",
    1258: "❄️",
    1261: "🌧️",
    1264: "🌧️",
    1273: "⛈️",
    1276: "⛈️",
    1279: "🌨️",
    1282: "🌨️"
}

def get_weather_emoji(icon_code, is_day=1):
    """
    Возвращает эмодзи погоды по коду иконки WeatherAPI.com.
    Для некоторых кодов использует флаг дня/ночи.
    """
    emoji_map = weather_emojis.get(icon_code)
    if isinstance(emoji_map, dict):
        return emoji_map.get("day" if is_day else "night", '❔')
    return emoji_map if emoji_map else '❔'


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

    # WeatherAPI может работать напрямую с названием города, без LocationKey
    # Просто сохраняем город, так как он будет использоваться в API-запросах
    user_data[user_id] = {"city_name": city}
    save_user_data(user_data)
    await update.message.reply_text(f"Город сохранён: {city}")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QR_PATH = os.path.join(BASE_DIR, 'assets', 'donate_qr.png')

async def donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик кнопки помощи проекту.
    
    Для отправки QR-кода необходимо:
    1. Создать папку `assets` в том же каталоге, что и `weather_bot.py`.
    2. Поместить ваш QR-код в эту папку и назвать файл `donate_qr.png`.
    """
    try:
        # ------------ ВАРИАНТ 1: ОТПРАВКА QR-КОДА (сейчас активен) ------------
        # Для активации этого блока убедитесь, что у вас есть папка 'assets'
        # с изображением QR-кода 'donate_qr.png'
        if not os.path.exists(QR_PATH):
            await update.message.reply_text("QR-код для доната не найден. Пожалуйста, свяжитесь с автором бота.")
            return
        with open(QR_PATH, 'rb') as qr:
            await update.message.reply_photo(
                photo=qr,
                caption="Спасибо за поддержку проекта! 💙\nОтсканируй QR-код СБП для перевода 🙏"
            )
        
        # ------------ ВАРИАНТ 2: ОТПРАВКА ТЕКСТОВОГО СООБЩЕНИЯ (закомментирован) ------------
        # Чтобы использовать этот вариант, закомментируйте код выше и раскомментируйте код ниже.
        # await update.message.reply_text(
        #      "Спасибо за поддержку проекта! 💙\n"
        #      "Пожалуйста, свяжитесь с автором (@space_ranger3209) для получения реквизитов 🙏"
        # )
    except Exception as e:
        await update.message.reply_text("Не удалось отправить QR-код 😢")
        print(f"Ошибка при отправке donate QR: {type(e).__name__}: {e}")

async def forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки прогноза на 5 дней."""
    user_id = str(update.message.from_user.id)
    user_info = user_data.get(user_id)
    if not user_info or not user_info.get("city_name"):
        await update.message.reply_text("Сначала укажи город. Нажми 📍 Сменить город")
        return

    city_name = user_info.get("city_name")
    text = get_forecast(city_name)
    await update.message.reply_text(text)

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Об авторе'."""
    await update.message.reply_text(
        "🤖""Привет! Я - бот прогноза погоды\n"
            "\n\nЕсли у вас есть предложения или вы хотите связаться пишите в телеграмм\n"
            "Автор: Сергей Сергиенко\n"
            "Telegram: @space_ranger3209\n" 
            "Github: https://github.com/sergo100\n"
            "© 2025 Все права защищены" 
        
        "\n\nЕсли хочешь поддержать проект, нажми 💸 Помочь проекту"   
        
    )

# ------------------ ПОГОДА ------------------

def get_weather(city_name):
    """Получает текущую погоду для города с WeatherAPI.com."""
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHERAPI_TOKEN}&q={city_name}&lang=ru"
        response = requests.get(url)
        data = response.json()
        
        # Добавлено для отладки: выводим статус ответа и сам ответ
        print(f"Запрос к API: {url}")
        print(f"Статус ответа: {response.status_code}")
        print(f"Тело ответа: {data}")

        if response.status_code == 200:
            temperature = data['current']['temp_c']
            description = data['current']['condition']['text']
            icon_code = data['current']['condition']['code']
            is_day = data['current']['is_day']
            emoji = get_weather_emoji(icon_code, is_day)

            return f"Погода в {city_name}: {emoji} {description}, {temperature}°C"
        elif response.status_code == 400 and 'error' in data:
            return f"Ошибка: {data['error']['message']}. Проверь название города."
        else:
            return "Не удалось получить погоду. Пожалуйста, попробуйте снова."

    except Exception as e:
        print(f"Ошибка при получении погоды WeatherAPI: {e}")
        return "Не удалось получить погоду. Проверь название города."

def get_forecast(city_name):
    """Получает прогноз на 5 дней с WeatherAPI.com."""
    try:
        url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHERAPI_TOKEN}&q={city_name}&days=5&lang=ru"
        response = requests.get(url)
        data = response.json()
        
        # Добавлено для отладки: выводим статус ответа и сам ответ
        print(f"Запрос к API: {url}")
        print(f"Статус ответа: {response.status_code}")
        print(f"Тело ответа: {data}")

        if response.status_code == 200:
            result = f"Прогноз погоды в {city_name} (5 дней):\n"
            forecast_items = data['forecast']['forecastday']

            for item in forecast_items:
                date = datetime.datetime.strptime(item['date'], '%Y-%m-%d').date()
                temperature_max = item['day']['maxtemp_c']
                temperature_min = item['day']['mintemp_c']
                description = item['day']['condition']['text']
                icon_code = item['day']['condition']['code']
                emoji = get_weather_emoji(icon_code)

                result += f"{date}: {emoji} {description}, от {temperature_min}°C до {temperature_max}°C\n"
            
            return result
        elif response.status_code == 400 and 'error' in data:
            return f"Ошибка: {data['error']['message']}. Проверь название города."
        else:
            return "Ошибка при получении прогноза. Попробуй снова."

    except Exception as e:
        print(f"Ошибка при получении прогноза WeatherAPI: {e}")
        return "Ошибка при получении прогноза. Попробуй снова."

# ------------------ РАСПИСАНИЕ И РАССЫЛКИ ------------------

async def send_daily_weather(context: ContextTypes.DEFAULT_TYPE):
    """Задача для ежедневной рассылки погоды."""
    for user_id, user_info in user_data.items():
        city_name = user_info.get("city_name")
        if city_name:
            text = get_weather(city_name)
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
                text="🔄 Бот обновлён! Теперь используется новый API погоды.\nНажмите /start, и введите название вашего города заново, чтобы изменения вступили в силу."
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
    app.job_queue.run_once(send_update_notification, 0)
    
    # Ежедневная рассылка погоды в 8:00
    app.job_queue.run_daily(send_daily_weather, time=datetime.time(hour=8, minute=0))

    # Запускаем бота
    app.run_polling()
