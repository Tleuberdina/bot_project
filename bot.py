import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes,
    ConversationHandler
)
import database as db
import google_sheets as gs

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
NAME, = range(1)

# Клавиатура для удобства
main_keyboard = ReplyKeyboardMarkup(
    [['/my', '/check'], ['/export', '/help']],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    user_id = update.effective_user.id
    
    # Проверяем, зарегистрирован ли пользователь
    user = db.get_user_by_telegram_id(user_id)
    
    if user:
        await update.message.reply_text(
            f"С возвращением, {user['name']}!\n"
            f"Используйте команды:\n"
            f"/my - мои процессы\n"
            f"/check <дата время> - проверить напоминания\n"
            f"/export - выгрузить в Google Sheets\n"
            f"/help - справка",
            reply_markup=main_keyboard
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "Добро пожаловать! Для регистрации введите ваше имя (как в бизнес-процессах):"
        )
        return NAME

async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Регистрация имени пользователя."""
    name = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Сохраняем пользователя
    db.register_user(user_id, name, update.effective_user.username)
    
    await update.message.reply_text(
        f"Отлично, {name}! Вы успешно зарегистрированы.\n"
        f"Используйте команды:\n"
        f"/my - мои процессы\n"
        f"/check <дата время> - проверить напоминания\n"
        f"/export - выгрузить в Google Sheets",
        reply_markup=main_keyboard
    )
    return ConversationHandler.END

async def my_processes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать процессы пользователя."""
    user_id = update.effective_user.id
    user = db.get_user_by_telegram_id(user_id)
    
    if not user:
        await update.message.reply_text(
            "Сначала зарегистрируйтесь! Используйте /start"
        )
        return
    
    processes = db.get_processes_by_responsible(user['name'])
    
    if not processes:
        await update.message.reply_text("У вас нет закрепленных бизнес-процессов.")
        return
    
    response = "📋 Ваши бизнес-процессы:\n\n"
    for process in processes:
        response += f"• {process['name']}\n"
        response += f"  Периодичность: {process['frequency']}\n"
        response += f"  Дедлайн: {process['deadline_time']}\n"
        response += f"  Напоминания: {process['reminder1']}, {process['reminder2']}\n\n"
    
    await update.message.reply_text(response)

async def check_deadlines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверить напоминания для указанного времени."""
    user_id = update.effective_user.id
    user = db.get_user_by_telegram_id(user_id)
    
    if not user:
        await update.message.reply_text("Сначала зарегистрируйтесь! Используйте /start")
        return
    
    # Проверяем аргументы
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Использование: /check <дата> <время>\n"
            "Пример: /check 15-12-2025 09:00"
        )
        return
    
    try:
        date_str = f"{context.args[0]} {context.args[1]}"
        check_time = datetime.strptime(date_str, "%d-%m-%Y %H:%M")
        
    except ValueError:
        await update.message.reply_text(
            "Неверный формат даты!\n"
            "Используйте: ДД-ММ-ГГГГ ЧЧ:ММ\n"
            "Пример: /check 15-12-2025 09:00"
        )
        return
    
    processes = db.get_processes_by_responsible(user['name'])
    
    if not processes:
        await update.message.reply_text("У вас нет закрепленных бизнес-процессов.")
        return
    
    response = f"⏰ Напоминания на {check_time.strftime('%d.%m.%Y %H:%M')}:\n\n"
    
    for process in processes:
        # Преобразуем время дедлайна в datetime для сегодняшней даты
        deadline_time = datetime.strptime(process['deadline_time'], "%H:%M").time()
        deadline_today = datetime.combine(check_time.date(), deadline_time)
        
        # Если дедлайн уже прошел для сегодняшнего дня, берем на следующий день
        if deadline_today < check_time:
            deadline_today += timedelta(days=1)
        
        time_until_deadline = deadline_today - check_time
        hours_until = time_until_deadline.total_seconds() / 3600
        
        # Получаем настройки напоминаний
        reminder1 = int(process['reminder1'].replace('ч', ''))
        reminder2 = int(process['reminder2'].replace('ч', ''))
        
        reminders = []
        if abs(hours_until - reminder1) < 0.5:  # допуск ±30 минут
            reminders.append(f"Первое напоминание ({reminder1}ч до дедлайна)")
        if abs(hours_until - reminder2) < 0.5:
            reminders.append(f"Второе напоминание ({reminder2}ч до дедлайна)")
        
        if reminders:
            response += f"🔔 {process['name']}:\n"
            for reminder in reminders:
                response += f"  • {reminder}\n"
            response += f"  Дедлайн: {deadline_today.strftime('%H:%M')}\n\n"
    
    if "🔔" not in response:
        response += "Нет активных напоминаний в указанное время."
    
    await update.message.reply_text(response)

async def export_to_sheets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выгрузить данные в Google Sheets."""
    try:
        spreadsheet_url = gs.export_processes_to_sheets()
        await update.message.reply_text(
            f"✅ Данные успешно выгружены в Google Sheets!\n"
            f"Ссылка: {spreadsheet_url}"
        )
    except Exception as e:
        logger.error(f"Ошибка при выгрузке в Google Sheets: {e}")
        await update.message.reply_text(
            "❌ Ошибка при выгрузке данных. Проверьте настройки Google API."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Справка по командам"""
    help_text = """
📚 Доступные команды:

/start - Начать работу с ботом
/my - Показать мои бизнес-процессы
/check <дата время> - Проверить напоминания
    Пример: /check 15-12-2025 09:00
/export - Выгрузить все процессы в Google Sheets
/help - Показать эту справку

📝 Пример использования:
1. Зарегистрируйтесь через /start
2. Посмотрите свои процессы через /my
3. Проверьте напоминания:
   /check 15-12-2025 09:00
"""
    await update.message.reply_text(help_text)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена регистрации."""
    await update.message.reply_text(
        "Регистрация отменена.",
        reply_markup=main_keyboard
    )
    return ConversationHandler.END

def main():
    """Запуск бота"""
    # Создаем Application
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    
    # Создаем базу данных и добавляем тестовые данные
    db.init_database()
    db.add_sample_data()
    
    # Настраиваем обработчики
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('my', my_processes))
    application.add_handler(CommandHandler('check', check_deadlines))
    application.add_handler(CommandHandler('export', export_to_sheets))
    application.add_handler(CommandHandler('help', help_command))
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
