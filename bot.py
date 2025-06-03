# bot.py

import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    filters,
    CallbackQueryHandler,
)
from dotenv import load_dotenv
import os
import requests
from database import create_database, populate_database, get_plant, get_seasonal_tips

# Загружаем токен из .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Настройка логов
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создаем базу данных
create_database()
populate_database()  # Заполняем базу данных

# Команда /start
async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    keyboard = [
        ["🌱 Рекомендации", "🛠 Помощь"],
        ["🌦 Погода", "🐛 Вредители"],
        ["📅 Календарь"],
    ]
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}! Я умный помощник для фермеров и садоводов.\n"
        "Доступные команды:\n"
        "/start - Начать работу\n"
        "/help - Помощь\n"
        "/weather [город] - Узнать погоду\n\n"
        "Или выберите опцию из меню:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )

# Функция для получения погоды
async def get_weather(update: Update, context: CallbackContext):
    if not WEATHER_API_KEY:
        await update.message.reply_text("Функция погоды не настроена администратором.")
        return

    if not context.args:
        await update.message.reply_text(
            "Пожалуйста, укажите город после команды, например: /weather Москва"
        )
        return

    city = " ".join(context.args)
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        response = requests.get(url)
        
        if response.status_code != 200:
            await update.message.reply_text("Город не найден или произошла ошибка. Попробуйте еще раз.")
            return

        data = response.json()
        weather = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]

        advice = ""
        if temp < 5:
            advice = "❄️ Холодно! Укройте теплолюбивые растения."
        elif temp > 30:
            advice = "☀️ Жарко! Увеличьте полив."

        message = (
            f"🌦 Погода в {city}:\n"
            f"• Состояние: {weather}\n"
            f"• Температура: {temp}°C\n"
            f"• Влажность: {humidity}%\n"
            f"• Ветер: {wind} м/с\n"
            f"\n{advice}"
        )

        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Ошибка при получении погоды: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text.lower()

    if text == "помощь" or text == "🛠 помощь":
        await show_help(update)
    elif text == "рекомендации" or text == "🌱 рекомендации":
        await show_plant_options(update)
    elif text == "вредители" or text == "🐛 вредители":
        await show_pests_menu(update)
    elif text == "календарь" or text == "📅 календарь":
        await show_seasonal_tips(update)
    elif text == "погода" or text == "🌦 погода":
        await update.message.reply_text(
            "Введите команду в формате: /weather [город]. Например: /weather Москва"
        )
    elif text in ["есль", "лиственница", "акация", "боярышник", "бузина", "герань", "флокс", "ирис", "пион", "лилейник", "петуния", "георгин", "ипомея", "яблоня", "груша", "клематис", "гацания"]:  
        plant = get_plant(text)
        if plant and len(plant) == 5:
            await show_plant_info(update, plant)
        else:
            await update.message.reply_text("Информация о растении неполная или отсутствует.")
    else:
        await update.message.reply_text(
            "Я не нашел информации по вашему запросу. Попробуйте что-то из меню."
        )

async def show_help(update: Update):
    help_text = (
        "🛠 *Доступные команды и функции:*\n\n"
        "🌱 *Рекомендации* - Советы по уходу за растениями\n"
        "🌦 *Погода* - Прогноз погоды для вашего региона\n"
        "🐛 *Вредители* - Информация о вредителях и борьбе с ними\n"
        "📅 *Календарь* - Сезонные советы для садоводов\n\n"
    )
    await update.message.reply_text(help_text)

async def show_plant_options(update: Update, page=0):
    all_plants = [
        ("Ель", "plant_ель"),
        ("Лиственница", "plant_лиственница"),
        ("Акация", "plant_акация"),
        ("Боярышник", "plant_боярышник"),
        ("Бузина", "plant_бузина"),
        ("Герань", "plant_герань"),
        ("Флокс", "plant_флокс"),
        ("Ирис", "plant_ирис"),
        ("Пион", "plant_пион"),
        ("Лилейник", "plant_лилейник"),
        ("Петуния", "plant_петуния"),
        ("Георгин", "plant_георгин"),
        ("Ипомея", "plant_ипомея"),
        ("Яблоня", "plant_яблоня"),
        ("Груша", "plant_груша"),
        ("Клематис", "plant_клематис"),
        ("Гацания", "plant_гацания"),
    ]
    
    plants_per_page = 5
    pages = [all_plants[i:i + plants_per_page] for i in range(0, len(all_plants), plants_per_page)]
    total_pages = len(pages)
    current_page = pages[page] if page < total_pages else pages[-1]
    
    keyboard = [
        [InlineKeyboardButton(name, callback_data=callback)] 
        for name, callback in current_page
    ]
    
    if total_pages > 1:
        navigation_buttons = []
        for i in range(total_pages):
            if i == page:
                navigation_buttons.append(InlineKeyboardButton(f"· {i+1} ·", callback_data=f"plant_page_{i}"))
            else:
                navigation_buttons.append(InlineKeyboardButton(str(i+1), callback_data=f"plant_page_{i}"))
        keyboard.append(navigation_buttons)
    
    text = f"🌿 Рекомендации по садовой культуре (страница {page+1}/{total_pages}). Выберите растение:"
    
    if isinstance(update, Update) and update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    try:
        data = query.data

        if data.startswith("plant_page_"):
            page = int(data.split("_")[2])
            await show_plant_options(update, page)
        
        elif data.startswith("plant_"):
            plant_name = data.split("_")[1]
            plant_data = get_plant(plant_name)
            if plant_data:
                name, description, care, pests, diseases = plant_data
                message = (
                    f"🌱 *{name.capitalize()}*\n\n"
                    f"{description}\n\n"
                    f"*Уход:*\n{care}\n\n"
                    f"*Основные вредители:* {pests}\n"
                    f"*Болезни:* {diseases}"
                )
                await query.message.reply_text(message)
            else:
                await query.message.reply_text("Информация о растении не найдена.")
        
        elif data.startswith("pest_"):
            pest = data.split("_")[1]
            tips = {
                "Тля": "• Опрыскивайте мыльным раствором с золой\n• Привлекайте божьих коровок\n• Используйте Фитоверм",
                "Паутинный клещ": "• Опрыскивайте растения холодной водой\n• Применяйте акарициды (Актара, Фитоверм)\n• Увеличьте влажность",
                "Белокрылка": "• Используйте желтые клеевые ловушки\n• Применяйте инсектициды (Актара)\n• Удаляйте пораженные листья",
                "Колорадский жук": "• Собирайте жуков вручную\n• Используйте препараты (Корадо, Актара)\n• Сажайте растения-репелленты",
            }
            await query.message.reply_text(f"🐛 *Борьба с {pest}:*\n\n{tips.get(pest, 'Информация отсутствует')}")
        
        elif data.startswith("season_"):
            season = data.split("_")[1]
            tips = get_seasonal_tips(season)
            if tips:
                await query.message.reply_text(f"📅 *Советы на {season}у:*\n\n{tips[0]}")
            else:
                await query.message.reply_text("Советы для этого сезона отсутствуют.")
    
    except Exception as e:
        logger.error(f"Ошибка в обработчике кнопок: {e}", exc_info=True)
        await query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте еще раз.")

async def show_plant_info(update: Update, plant):
    if plant is None:
        await update.message.reply_text("Информация о растении не найдена.")
        return

    try:
        name, description, care, pests, diseases = plant
        message = f"🌱 *{name.capitalize()}*\n\n{description}\n\n*Уход:*\n{care}\n\n*Основные вредители:* {pests}\n*Болезни:* {diseases}"
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Ошибка при обработке данных растения: {e}")
        await update.message.reply_text("Произошла ошибка при обработке данных о растении.")

async def show_pests_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("Тля", callback_data="pest_Тля")],
        [InlineKeyboardButton("Паутинный клещ", callback_data="pest_Паутинный клещ")],
        [InlineKeyboardButton("Белокрылка", callback_data="pest_Белокрылка")],
        [InlineKeyboardButton("Колорадский жук", callback_data="pest_Колорадский жук")],
    ]
    await update.message.reply_text(
        "Выберите вредителя для получения информации:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def show_seasonal_tips(update: Update):
    keyboard = [
        [InlineKeyboardButton("Весна", callback_data="season_весна")],
        [InlineKeyboardButton("Лето", callback_data="season_лето")],
        [InlineKeyboardButton("Осень", callback_data="season_осень")],
        [InlineKeyboardButton("Зима", callback_data="season_зима")],
    ]
    await update.message.reply_text(
        "Выберите сезон для получения советов:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# Обработчик inline кнопок
async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    try:
        data = query.data

        if data.startswith("plant_page_"):
            page = int(data.split("_")[2])
            await show_plant_options(update, page)
        
        elif data.startswith("plant_"):
            plant_name = data.split("_")[1]
            plant_data = get_plant(plant_name)
            if plant_data:
                name, description, care, pests, diseases = plant_data
                message = (
                    f"🌱 *{name.capitalize()}*\n\n"
                    f"{description}\n\n"
                    f"*Уход:*\n{care}\n\n"
                    f"*Основные вредители:* {pests}\n"
                    f"*Болезни:* {diseases}"
                )
                # Редактируем текущее сообщение вместо отправки нового
                await query.edit_message_text(
                    text=message,
                    reply_markup=None  # Убираем клавиатуру
                )
            else:
                await query.edit_message_text("Информация о растении не найдена.")
        
        elif data.startswith("pest_"):
            pest = data.split("_")[1]
            tips = {
                "Тля": "• Опрыскивайте мыльным раствором с золой\n• Привлекайте божьих коровок\n• Используйте Фитоверм",
                "Паутинный клещ": "• Опрыскивайте растения холодной водой\n• Применяйте акарициды (Актара, Фитоверм)\n• Увеличьте влажность",
                "Белокрылка": "• Используйте желтые клеевые ловушки\n• Применяйте инсектициды (Актара)\n• Удаляйте пораженные листья",
                "Колорадский жук": "• Собирайте жуков вручную\n• Используйте препараты (Корадо, Актара)\n• Сажайте растения-репелленты",
            }
            await query.edit_message_text(
                text=f"🐛 *Борьба с {pest}:*\n\n{tips.get(pest, 'Информация отсутствует')}",
                reply_markup=None
            )
        
        elif data.startswith("season_"):
            season = data.split("_")[1]
            tips = get_seasonal_tips(season)
            if tips:
                await query.edit_message_text(
                    text=f"📅 *Советы на {season}у:*\n\n{tips[0]}",
                    reply_markup=None
                )
            else:
                await query.edit_message_text("Советы для этого сезона отсутствуют.")
    
    except Exception as e:
        logger.error(f"Ошибка в обработчике кнопок: {e}", exc_info=True)
        await query.edit_message_text("Произошла ошибка. Пожалуйста, попробуйте еще раз.")

# Обработчик ошибок  
async def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(f"Ошибка при обработке сообщения: {context.error}")
    if update.message:
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте еще раз.")

# Запуск бота
def main():
    application = Application.builder().token(TOKEN).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", show_help))
    application.add_handler(CommandHandler("weather", get_weather))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Обработчик inline кнопок
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    logger.info("Бот запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()
