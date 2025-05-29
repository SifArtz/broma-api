# Broma API Wrapper

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

Это FastAPI-обертка для работы с API сервиса Broma, предоставляющая удобные endpoints для управления релизами и их доставками.

## 📌 Возможности

- Получение метаданных релиза по UPC-коду
- Просмотр информации о доставках релиза
- Выполнение отзывы с площадок релиза
- Простая интеграция с существующими системами

## 🚀 Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/broma-api-wrapper.git
cd broma-api-wrapper
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Запустите сервер:
```bash
uvicorn main:app --reload
```

Сервер будет доступен по адресу: `http://127.0.0.1:8000`

## 📚 Документация API

После запуска сервера документация доступна по адресам:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## 🔧 Endpoints

### Получение метаданных релиза
`GET /release`
- Параметры:
  - `upc_code`: UPC-код релиза
  - `access_token`: Токен доступа Broma API

### Получение информации о доставках
`GET /release_deliveries`
- Параметры:
  - `upc_code`: UPC-код релиза
  - `access_token`: Токен доступа Broma API

### Выполнение takedown операции
`POST /release_takedown`
- Параметры:
  - `upc_code`: UPC-код релиза
  - `access_token`: Токен доступа Broma API
- Заголовки:
  - `HMAC-Hash`: HMAC хэш
  - `HMAC-Timestamp`: HMAC метка времени

## ⚙️ Конфигурация

Базовый URL API Broma можно изменить в переменной `BASE_URL` в файле `main.py`.

## 🤝 Участие в разработке

Приветствуются pull requests и issue reports. Перед внесением изменений:

1. Форкните репозиторий
2. Создайте ветку с вашими изменениями (`git checkout -b feature/AmazingFeature`)
3. Зафиксируйте изменения (`git commit -m 'Add some AmazingFeature'`)
4. Запушьте изменения (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📜 Лицензия

Распространяется под лицензией MIT. См. файл `LICENSE` для подробностей.

## ✉️ Контакты

SifArtz

Project Link: [https://github.com/SifArtz/broma-api](https://github.com/SifArtz/broma-api)
