import os
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import database as db

# ID вашей Google таблицы (замените на свой)
SPREADSHEET_ID = '1XSrbyKF3wQv_6VJJzJ0ZHpzjWVv0dA3JU-g3M94gTRE'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_google_credentials():
    """Получение учетных данных Google."""
    # Создаем credentials из файла (для продакшена)
    # Или используем service account
    credentials = service_account.Credentials.from_service_account_file(
        'credentials.json', scopes=SCOPES
    )
    return credentials

def create_spreadsheet(service, title="Бизнес-процессы"):
    """Создать новую Google таблицу."""
    try:
        spreadsheet = {
            'properties': {
                'title': title,
                'locale': 'ru_RU'
            },
            'sheets': [{
                'properties': {
                    'title': 'Процессы',
                    'gridProperties': {
                        'rowCount': 100,
                        'columnCount': 10
                    }
                }
            }]
        }
        
        spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
        return spreadsheet['spreadsheetId'], spreadsheet['spreadsheetUrl']
    except HttpError as error:
        print(f"Ошибка при создании таблицы: {error}")
        return None, None

def export_processes_to_sheets():
    """Экспорт всех процессов в Google Sheets."""
    try:
        # Получаем учетные данные
        creds = get_google_credentials()
        service = build('sheets', 'v4', credentials=creds)
        
        # Получаем данные из базы
        processes = db.get_all_processes()
        
        # Подготавливаем данные для записи
        values = [
            ['ID', 'Название процесса', 'Ответственный', 'Периодичность', 
             'Время дедлайна', 'Первое напоминание', 'Второе напоминание', 'Дата создания']
        ]
        
        for process in processes:
            values.append([
                process['id'],
                process['name'],
                process['responsible'],
                process['frequency'],
                process['deadline_time'],
                process['reminder1'],
                process['reminder2'],
                process['created_at']
            ])
        
        # Обновляем таблицу
        body = {
            'values': values
        }
        
        # Если SPREADSHEET_ID не указан, создаем новую таблицу
        if SPREADSHEET_ID == 'YOUR_SPREADSHEET_ID':
            spreadsheet_id, spreadsheet_url = create_spreadsheet(service)
        else:
            spreadsheet_id = SPREADSHEET_ID
        
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Лист1!A1',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        # Форматируем таблицу
        format_spreadsheet(service, spreadsheet_id)
        
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        
    except Exception as e:
        print(f"Ошибка при экспорте в Google Sheets: {e}")
        raise

def format_spreadsheet(service, spreadsheet_id):
    """Форматирование Google таблицы."""
    try:
        requests = [
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {
                                'red': 0.2,
                                'green': 0.6,
                                'blue': 0.8
                            },
                            'textFormat': {
                                'bold': True,
                                'foregroundColor': {
                                    'red': 1.0,
                                    'green': 1.0,
                                    'blue': 1.0
                                }
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                }
            },
            {
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': 0,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': 8
                    }
                }
            }
        ]
        
        body = {
            'requests': requests
        }
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()
        
    except Exception as e:
        print(f"Ошибка при форматировании таблицы: {e}")
