import logging
import asyncpg
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация бота и базы данных
BOT_TOKEN = "ваш токен"
START_IMAGE_URL = "https://i.postimg.cc/TYyS5w9n/Flux-Dev-Create-a-captivating-book-cover-for-ITAYTSORSING-feat-1.jpg"
DB_CONFIG = {
    "user": "",
    "password": "",  
    "database": "",
    "host": "",
    "port": ,
}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Глобальный пул соединений
db_pool: asyncpg.pool.Pool = None

# ================== ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ ==================

async def create_db_pool():
    return await asyncpg.create_pool(
        **DB_CONFIG,
        min_size=1,
        max_size=10,
        max_inactive_connection_lifetime=60,
        timeout=30
    )

async def init_db(pool: asyncpg.pool.Pool):
    """Инициализация структуры базы данных"""
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(100),
                full_name VARCHAR(200) NOT NULL,
                registration_date TIMESTAMP DEFAULT NOW(),
                last_activity TIMESTAMP DEFAULT NOW()
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS services (
                service_id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS service_options (
                option_id SERIAL PRIMARY KEY,
                service_id INTEGER REFERENCES services(service_id) ON DELETE CASCADE,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                price VARCHAR(100)
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                request_id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                request_text TEXT NOT NULL,
                request_date TIMESTAMP DEFAULT NOW(),
                status VARCHAR(50) DEFAULT 'new',
                service_option_id INTEGER REFERENCES service_options(option_id) ON DELETE SET NULL
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS faq (
                faq_id SERIAL PRIMARY KEY,
                question VARCHAR(200) NOT NULL,
                answer TEXT NOT NULL
            )
        ''')

        # Заполняем начальные данные, если таблицы пустые
        if await conn.fetchval("SELECT COUNT(*) FROM services") == 0:
            await init_services_data(conn)
        if await conn.fetchval("SELECT COUNT(*) FROM faq") == 0:
            await init_faq_data(conn)

async def init_services_data(conn):
    """Инициализация данных об услугах"""
    web_dev_id = await conn.fetchval('''
        INSERT INTO services (name, description)
        VALUES ($1, $2)
        RETURNING service_id
    ''', "🌐 Веб-разработка", "Полный цикл разработки веб-приложений и сайтов")

    mobile_dev_id = await conn.fetchval('''
        INSERT INTO services (name, description)
        VALUES ($1, $2)
        RETURNING service_id
    ''', "📱 Мобильные приложения", "Разработка мобильных приложений для iOS и Android")

    # Варианты для веб-разработки
    await conn.execute('''
        INSERT INTO service_options (service_id, name, description, price)
        VALUES ($1, $2, $3, $4)
    ''', web_dev_id, "Лендинг",
       "• Адаптивный дизайн\n• Интеграция с CRM\n• SEO-оптимизация\n• Срок: 5-10 дней",
       "от 30 000₽")

    await conn.execute('''
        INSERT INTO service_options (service_id, name, description, price)
        VALUES ($1, $2, $3, $4)
    ''', web_dev_id, "Корпоративный сайт",
       "• Современный дизайн\n• Админ-панель\n• Мультиязычность\n• Срок: 2-3 недели",
       "от 80 000₽")

    await conn.execute('''
        INSERT INTO service_options (service_id, name, description, price)
        VALUES ($1, $2, $3, $4)
    ''', web_dev_id, "Интернет-магазин",
       "• Каталог товаров\n• Корзина и оплата\n• Интеграция с 1С\n• Срок: 3-4 недели",
       "от 150 000₽")

    # Варианты для мобильных приложений
    await conn.execute('''
        INSERT INTO service_options (service_id, name, description, price)
        VALUES ($1, $2, $3, $4)
    ''', mobile_dev_id, "Простое приложение",
       "• Кроссплатформенное\n• Базовый функционал\n• Срок: 3-4 недели",
       "от 120 000₽")

    await conn.execute('''
        INSERT INTO service_options (service_id, name, description, price)
        VALUES ($1, $2, $3, $4)
    ''', mobile_dev_id, "Приложение средней сложности",
       "• Нативный дизайн\n• API интеграции\n• Push-уведомления\n• Срок: 6-8 недели",
       "от 250 000₽")

    await conn.execute('''
        INSERT INTO service_options (service_id, name, description, price)
        VALUES ($1, $2, $3, $4)
    ''', mobile_dev_id, "Комплексное решение",
       "• Собственный бэкенд\n• Сложная логика\n• Высокая нагрузка\n• Срок: 3-6 месяцев",
       "от 500 000₽")

async def init_faq_data(conn):
    """Инициализация FAQ"""
    await conn.execute('''
        INSERT INTO faq (question, answer)
        VALUES ($1, $2)
    ''', "Что такое IT-аутсорсинг?",
       "IT-аутсорсинг — это передача задач по разработке и поддержке IT-решений внешней команде специалистов. "
       "Вы получаете качественный результат без необходимости содержать собственный IT-отдел.")

    await conn.execute('''
        INSERT INTO faq (question, answer)
        VALUES ($1, $2)
    ''', "Преимущества аутсорсинга",
       "• Экономия на зарплатах и оборудовании\n"
       "• Доступ к экспертам с разными навыками\n"
       "• Быстрый старт проектов\n"
       "• Гибкость в масштабировании\n"
       "• Предсказуемые расходы")

    await conn.execute('''
        INSERT INTO faq (question, answer)
        VALUES ($1, $2)
    ''', "Как оформить заказ?",
       "1. Опишите ваш проект через кнопку 'Оставить заявку'\n"
       "2. Мы оценим задачу и предложим решение\n"
       "3. Заключим договор и приступим к работе\n"
       "4. Вы получите готовый продукт в согласованные сроки")

# ================== ФУНКЦИИ ДЛЯ РАБОТЫ С БД ==================
async def clear_all_requests():
    """Очистка всех заявок из базы данных"""
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM requests")
        logger.info("Все заявки удалены из базы данных")

async def delete_request(request_id: int):
    """Удаление конкретной заявки"""
    async with db_pool.acquire() as conn:
        deleted = await conn.execute("DELETE FROM requests WHERE request_id = $1", request_id)
    return int(deleted.split()[-1]) > 0

async def delete_user(user_id: int):
    """Удаление пользователя и всех его заявок"""
    async with db_pool.acquire() as conn:
        deleted = await conn.execute("DELETE FROM users WHERE user_id = $1", user_id)
    return int(deleted.split()[-1]) > 0

async def delete_service(service_id: int):
    """Удаление услуги и связанных с ней вариантов"""
    async with db_pool.acquire() as conn:
        deleted = await conn.execute("DELETE FROM services WHERE service_id = $1", service_id)
    return int(deleted.split()[-1]) > 0

async def delete_faq(faq_id: int):
    """Удаление вопроса из FAQ"""
    async with db_pool.acquire() as conn:
        deleted = await conn.execute("DELETE FROM faq WHERE faq_id = $1", faq_id)
    return int(deleted.split()[-1]) > 0

async def get_all_requests():
    """Получение всех заявок"""
    async with db_pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM requests ORDER BY request_date DESC")

async def get_all_users():
    """Получение всех пользователей"""
    async with db_pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM users ORDER BY registration_date DESC")

async def get_all_services():
    """Получение всех услуг"""
    async with db_pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM services")

async def get_all_faq():
    """Получение всех вопросов FAQ"""
    async with db_pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM faq")

async def clear_all_requests():
    """Очистка всех заявок из базы данных"""
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM requests")
        logger.info("Все заявки удалены из базы данных")


async def register_user(user_id: int, username: str, full_name: str):
    """Регистрация/обновление пользователя"""
    async with db_pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO users (user_id, username, full_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) 
            DO UPDATE SET last_activity = NOW(), username = EXCLUDED.username, full_name = EXCLUDED.full_name
        ''', user_id, username, full_name)
    logger.info(f"Пользователь {user_id} зарегистрирован/обновлен")

async def create_request(user_id: int, request_text: str, service_option_id: int = None):
    """Создание новой заявки"""
    async with db_pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO requests (user_id, request_text, service_option_id)
            VALUES ($1, $2, $3)
        ''', user_id, request_text, service_option_id)
        request_id = await conn.fetchval("SELECT lastval()")
    return request_id

async def get_services():
    """Получение списка услуг"""
    async with db_pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM services")

async def get_service_options(service_id: int):
    """Получение вариантов для услуги"""
    async with db_pool.acquire() as conn:
        return await conn.fetch('''
            SELECT * FROM service_options 
            WHERE service_id = $1
        ''', service_id)

async def get_faq_questions():
    """Получение списка вопросов FAQ"""
    async with db_pool.acquire() as conn:
        return await conn.fetch("SELECT question FROM faq")

async def get_faq_answer(question: str):
    """Получение ответа на вопрос FAQ"""
    async with db_pool.acquire() as conn:
        return await conn.fetchval('''
            SELECT answer FROM faq 
            WHERE question = $1
        ''', question)

# ================== КЛАВИАТУРЫ ==================

def get_main_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🚨 IT-Аутсорсинг"),
        KeyboardButton(text="📞 Контакты"),
        KeyboardButton(text="❓ Частые вопросы")
    )
    builder.row(
        KeyboardButton(text="📨 Оставить заявку")
    )
    return builder.as_markup(resize_keyboard=True)

def get_back_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Назад")]],
        resize_keyboard=True
    )

def get_outsource_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🌐 Веб-разработка"),
        KeyboardButton(text="📱 Мобильные приложения")
    )
    builder.row(
        KeyboardButton(text="🔙 Назад")
    )
    return builder.as_markup(resize_keyboard=True)

def get_help_kb():
    builder = ReplyKeyboardBuilder()
    questions = dp["faq_questions"]  # Заполняется при старте
    for question in questions[:2]:
        builder.add(KeyboardButton(text=question["question"]))
    builder.row(
        KeyboardButton(text="Как оформить заказ?"),
        KeyboardButton(text="🔙 Назад")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


ADMIN_IDS = {}  # Замените на реальные ID администраторов

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав администратора")
        return
    
    text = (
        "👨‍💻 <b>Панель администратора</b>\n\n" 
        "Доступные команды:\n"
        "/requests - Просмотр всех заявок\n"
        "/users - Просмотр всех пользователей\n"
        "/services - Просмотр всех услуг\n"
        "/faq - Просмотр всех вопросов FAQ\n\n"
        "Для удаления используйте:\n"
        "/delete_request [id] - Удалить заявку\n"
        "/delete_user [id] - Удалить пользователя\n"
        "/delete_service [id] - Удалить услугу\n"
        "/delete_faq [id] - Удалить вопрос FAQ\n\n"
        "/clear_requests - Очистить все заявки"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("requests"))
async def show_requests(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав администратора")
        return
    
    requests = await get_all_requests()
    if not requests:
        await message.answer("Нет заявок в базе данных")
        return
    
    text = "📋 <b>Список заявок:</b>\n\n"
    for req in requests:
        text += (
            f"ID: {req['request_id']}\n"
            f"Пользователь: {req['user_id']}\n"
            f"Дата: {req['request_date'].strftime('%Y-%m-%d %H:%M')}\n"
            f"Статус: {req['status']}\n"
            f"Текст: {req['request_text'][:50]}...\n\n"
        )
    
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("users"))
async def show_users(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав администратора")
        return
    
    users = await get_all_users()
    if not users:
        await message.answer("Нет пользователей в базе данных")
        return
    
    text = "👥 <b>Список пользователей:</b>\n\n"
    for user in users:
        text += (
            f"ID: {user['user_id']}\n"
            f"Имя: {user['full_name']}\n"
            f"Username: @{user['username']}\n"
            f"Дата регистрации: {user['registration_date'].strftime('%Y-%m-%d')}\n\n"
        )
    
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("services"))
async def show_services(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав администратора")
        return
    
    services = await get_all_services()
    if not services:
        await message.answer("Нет услуг в базе данных")
        return
    
    text = "🛠 <b>Список услуг:</b>\n\n"
    for service in services:
        text += (
            f"ID: {service['service_id']}\n"
            f"Название: {service['name']}\n"
            f"Описание: {service['description'][:50]}...\n\n"
        )
    
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("faq"))
async def show_faq(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав администратора")
        return
    
    faqs = await get_all_faq()
    if not faqs:
        await message.answer("Нет вопросов в FAQ")
        return
    
    text = "❓ <b>Список вопросов FAQ:</b>\n\n"
    for faq in faqs:
        text += (
            f"ID: {faq['faq_id']}\n"
            f"Вопрос: {faq['question']}\n"
            f"Ответ: {faq['answer'][:50]}...\n\n"
        )
    
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("delete_request"))
async def delete_request_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав администратора")
        return
    
    try:
        request_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.answer("❌ Использование: /delete_request [id]")
        return
    
    if await delete_request(request_id):
        await message.answer(f"✅ Заявка #{request_id} удалена")
    else:
        await message.answer("❌ Заявка не найдена")

@dp.message(Command("delete_user"))
async def delete_user_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав администратора")
        return
    
    try:
        user_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.answer("❌ Использование: /delete_user [id]")
        return
    
    if await delete_user(user_id):
        await message.answer(f"✅ Пользователь #{user_id} удален")
    else:
        await message.answer("❌ Пользователь не найден")

@dp.message(Command("delete_service"))
async def delete_service_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав администратора")
        return
    
    try:
        service_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.answer("❌ Использование: /delete_service [id]")
        return
    
    if await delete_service(service_id):
        await message.answer(f"✅ Услуга #{service_id} удалена")
    else:
        await message.answer("❌ Услуга не найдена")

@dp.message(Command("delete_faq"))
async def delete_faq_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав администратора")
        return
    
    try:
        faq_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.answer("❌ Использование: /delete_faq [id]")
        return
    
    if await delete_faq(faq_id):
        await message.answer(f"✅ Вопрос FAQ #{faq_id} удален")
    else:
        await message.answer("❌ Вопрос не найден")

@dp.message(Command("clear_requests"))
async def clear_requests_cmd(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав администратора")
        return
    
    await clear_all_requests()
    await message.answer("✅ Все заявки удалены")


# ================== ОБРАБОТЧИКИ СООБЩЕНИЙ ==================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await register_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )
    try:
        await message.answer_photo(
            photo=START_IMAGE_URL,
            caption="🛠 <b>IT-Аутсорсинг PRO</b>\n\n"
                    "Профессиональная разработка веб и мобильных решений\n\n"
                    "Выберите нужный вариант:",
            parse_mode="HTML",
            reply_markup=get_main_kb()
        )
    except Exception as e:
        logger.error(f"Ошибка загрузки изображения: {e}")
        await message.answer(
            "🛠 <b>Добро пожаловать в IT-Аутсорсинг PRO</b>\n\n"
            "Выберите действие:",
            parse_mode="HTML",
            reply_markup=get_main_kb()
        )

@dp.message(F.text == "🚨 IT-Аутсорсинг")
async def outsource_menu(message: types.Message):
    await message.answer(
        "🖥 <b>Направления разработки:</b>\n\n"
        "Выберите интересующее вас направление:",
        parse_mode="HTML",
        reply_markup=get_outsource_kb()
    )


@dp.message(Command("clear_db"))
async def clear_db_command(message: types.Message):
    if message.from_user.id == 1072196801:  
        await clear_all_requests()
        await message.answer("✅ Все заявки удалены")
    else:
        await message.answer("⛔ У вас нет прав на эту операцию")    

@dp.message(F.text.in_(["🌐 Веб-разработка", "📱 Мобильные приложения"]))
async def service_menu_handler(message: types.Message):
    services = await get_services()
    service = next((s for s in services if s["name"] == message.text), None)
    if not service:
        await message.answer("Услуга не найдена")
        return

    options = await get_service_options(service["service_id"])
    builder = ReplyKeyboardBuilder()
    for option in options:
        builder.add(KeyboardButton(text=option["name"]))
    builder.add(KeyboardButton(text="🔙 Назад"))
    builder.adjust(1)

    await message.answer(
        f"<b>{service['name']}</b>\n\n{service['description']}\n\nВыберите тип проекта:",
        parse_mode="HTML",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

@dp.message(F.text == "❓ Частые вопросы")
async def help_handler(message: types.Message):
    await message.answer(
        "❓ <b>Часто задаваемые вопросы:</b>\n"
        "Выберите интересующий вас вопрос:",
        parse_mode="HTML",
        reply_markup=get_help_kb()
    )


@dp.message(F.text == "📞 Контакты")
async def contacts_handler(message: types.Message):
    await message.answer(
        "📞 <b>Наши контакты:</b>\n\n"
        "Телефон: +7 (912) 345-67-89\n"
        "Email: it-aytsors@gmail.com\n"
        "Telegram: @it_outsourcing_support\n\n"
        "Работаем с 9:00 до 18:00 по МСК",
        parse_mode="HTML",
        reply_markup=get_back_kb()
    )


@dp.message(F.text == "📨 Оставить заявку")
async def create_request_handler(message: types.Message):
    await message.answer(
        "✍️ <b>Опишите ваш проект:</b>\n\n"
        "Укажите следующую информацию:\n"
        "1. Тип проекта (веб/мобильное)\n"
        "2. Основные требования\n"
        "3. Желаемые сроки\n"
        "4. Бюджет (если есть)\n\n"
        "Наш менеджер свяжется с вами для уточнения деталей.",
        parse_mode="HTML",
        reply_markup=get_back_kb()
    )

@dp.message(F.text == "🔙 Назад")
async def back_handler(message: types.Message):
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_kb()
    )

@dp.message()
async def process_any_message(message: types.Message):
    # Проверяем, является ли сообщение вопросом из FAQ
    faq_answer = await get_faq_answer(message.text)
    if faq_answer:
        await message.answer(
            f"<b>{message.text}</b>\n\n{faq_answer}",
            parse_mode="HTML",
            reply_markup=get_help_kb()
        )
        return

    # Проверяем, является ли сообщение вариантом услуги
    async with db_pool.acquire() as conn:
        option = await conn.fetchrow('''
            SELECT so.*, s.name as service_name 
            FROM service_options so
            JOIN services s ON so.service_id = s.service_id
            WHERE so.name = $1
        ''', message.text)

    if option:
        await message.answer(
            f"<b>{option['name']}</b>\n\n"
            f"{option['description']}\n\n"
            f"<b>Стоимость:</b> {option['price']}\n\n"
            "✍️ Для заказа нажмите кнопку 'Оставить заявку' или напишите:\n"
            "1. Описание проекта\n2. Желаемые сроки\n3. Бюджет (если есть)",
            parse_mode="HTML",
            reply_markup=get_back_kb()
        )
        return

    # Если это не команда и не известный текст, считаем заявкой
    request_id = await create_request(
        user_id=message.from_user.id,
        request_text=message.text
    )

    await message.answer(
        "✅ <b>Ваше сообщение принято как заявка!</b>\n\n"
        f"Номер заявки: #{request_id}\n"
        "Мы свяжемся с вами в ближайшее время для уточнения деталей.",
        parse_mode="HTML",
        reply_markup=get_main_kb()
    )

# ================== ЗАПУСК БОТА ==================

async def on_startup():
    global db_pool
    db_pool = await create_db_pool()
    await init_db(db_pool)
    dp["faq_questions"] = await get_faq_questions()
    logger.info("Бот запущен и БД инициализирована")

async def on_shutdown():
    await db_pool.close()
    await bot.close()
    logger.info("Пул соединений закрыт и бот остановлен")

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен вручную")