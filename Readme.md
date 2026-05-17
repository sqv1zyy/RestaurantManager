# 🍽️ RestaurantManager

**Система управления рестораном с базой данных PostgreSQL и графическим интерфейсом на Python**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-336791.svg)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 Описание

RestaurantManager — это полноценная система автоматизации работы ресторана, разработанная в рамках учебного курса по базам данных. Приложение позволяет управлять заказами, персоналом, складом ингредиентов, бронированием столов и аналитикой продаж.

### ✨ Основные возможности

- 📊 **Управление заказами** — создание, отслеживание статуса, история
- 👨‍🍳 **Кухня** — контроль приготовления блюд, учет ингредиентов
- 👥 **Персонал** — управление сотрудниками, сменами, расчет зарплаты
- 🪑 **Бронирование** — система резервирования столов
- 📈 **Аналитика** — отчеты по продажам, популярные блюда, выручка
- 🧾 **Чеки** — генерация PDF-чеков
- 📦 **Склад** — учет ингредиентов, сроков годности, поставок

---

## 🖼️ Скриншоты

### Главное меню
![Главное меню](screenshots/main_menu.png)

### Управление заказами
![Заказы](screenshots/orders.png)

### Аналитика продаж
![Аналитика](screenshots/analytics.png)

### Управление сотрудниками
![Сотрудники](screenshots/employees.png)

---

## 🚀 Установка

### Требования

- Python 3.8 или выше
- PostgreSQL 12 или выше
- Git

### Пошаговая инструкция

1. **Клонируйте репозиторий**
   ```bash
   git clone https://github.com/yourusername/RestaurantManager.git
   cd RestaurantManager
Создайте базу данных PostgreSQL

sql
CREATE DATABASE restaurant_db;
Выполните SQL-скрипт создания таблиц (файл database.sql)

bash
psql -U postgres -d restaurant_db -f database.sql
Настройте подключение к БД

Откройте config.py и укажите ваши параметры:

python
DB_CONFIG = {
    "host": "localhost",
    "database": "restaurant_db",
    "user": "postgres",
    "password": "your_password"
}
Установите зависимости

bash
pip install -r requirements.txt
Запустите приложение

bash
python main.py
📚 Использование
Вход в систему
При первом запуске используйте учетные данные сотрудника, созданного в базе данных:

Логин: телефон сотрудника

Пароль: установленный при создании

Роли пользователей
Администратор/Менеджер — полный доступ ко всем функциям

Повар — управление заказами на кухне, учет ингредиентов

Официант — создание заказов, просмотр меню

🏗️ Структура проекта
text
RestaurantManager/
├── forms/                  # Модули интерфейса
│   ├── all_orders.py      # Все заказы
│   ├── cook_orders.py     # Заказы для кухни
│   ├── employee_management.py
│   ├── new_dish.py        # Создание блюд
│   ├── report.py          # Отчеты
│   ├── salary.py          # Расчет зарплаты
│   └── ...
├── screenshots/           # Скриншоты интерфейса
├── config.py             # Конфигурация БД
├── db.py                 # Работа с базой данных
├── main.py               # Точка входа
├── requirements.txt      # Зависимости
├── database.sql          # SQL-схема БД
└── README.md
🛠️ Технологический стек
Backend: Python 3.8+

GUI: Tkinter, ttk

Database: PostgreSQL 12+

Libraries:

psycopg2 — драйвер PostgreSQL

reportlab — генерация PDF

pillow — работа с изображениями

tkcalendar — календарь

babel — локализация

📊 Схема базы данных
Основные таблицы:

Employee — сотрудники

Post — должности

Shift — смены

TableInfo — столы

Orderr — заказы

Order_item — позиции заказа

Dish — блюда

Recipe — рецепты

Ingredient — ингредиенты

🎓 Учебный проект
Проект разработан в рамках курса "Базы данных" и демонстрирует:

Проектирование реляционной базы данных

Нормализацию данных

Создание хранимых процедур и функций

Работу с транзакциями

Разработку клиент-серверного приложения

👨‍💻 Автор
Ваше Имя
GitHub: @yourusername
Email: your.email@example.com

<div align="center">
Made with ❤️ using Python & PostgreSQL

⭐ Если вам понравился проект, поставьте звезду на GitHub!

</div> ```
