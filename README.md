# Telegram Business Process Bot
## Описание:
Telegram-бот для управления бизнес-процессами.
Бот регистрирует пользователей, напоминает о задачах и выгружает данные в Google Sheets.

### Технологии:
- Язык программирования — Python
- База данных — SQLite3, SQLAlchemy
- Telegram-бот — python-telegram-bot
- Интеграции — Google Sheets API v4, Google Auth Library
- Конфигурация — python-dotenv

### Команда для запуска проекта локально: python bot.py

### Шаги развертывания
1. Клонировать репозиторий и перейти в него в командной строке:
   #### git clone git@github.com:Tleuberdina/bot_project.git
   #### cd bot_project
3. Cоздать и активировать виртуальное окружение:
   #### python -m venv venv
   #### source venv/Scripts/activate
4. Установить зависимости из файла requirements.txt:
   #### python -m pip install -- upgrade pip
   #### pip install -r requirements.txt
5. Укажите в файле config/.env данные:
   #### TELEGRAM_BOT_TOKEN=ваш_токен
   #### GOOGLE_SPREADSHEET_ID=ваш_id_в_таблице
   #### в ссылке на Вашу таблицу указан id таблицы
   #### https://docs.google.com/spreadsheets/d/здесь_указан_ваш_id/edit?gid=0#gid=0
6. Настроить Google Sheets API:
   #### Создайте сервисный аккаунт
   #### Скачайте файл credentials.json
   #### Поместите его в корневую папку проекта
7. Настроить доступ к Google таблице:
   #### Откройте вашу Google таблицу
   #### Нажмите "Настройки доступа"
   #### Добавьте email из credentials.json (поле client_email) как редактора
