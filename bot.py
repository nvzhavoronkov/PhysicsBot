"""
PHYSICS BOT - Telegram бот для изучения физики и подготовки к олимпиадам
Автор: Жаворонков Ярослав Николаевич, 7Д класс
Руководитель: Жаворонков Николай Валерьевич, ИТ-директор
Версия: 2.1 (исправленная)
Дата: 2026 год
"""

import logging
import random
import asyncio
from datetime import datetime
from typing import Dict, Any
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramUnauthorizedError, TelegramBadRequest

# ============================================================================
# 1. НАСТРОЙКА ЛОГИРОВАНИЯ
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# 2. ТОКЕН БОТА
# ============================================================================
BOT_TOKEN = os.getenv('BOT_TOKEN')
if BOT_TOKEN is None:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена!")

# ============================================================================
# 3. База задач по физике 7-11 классы
# ============================================================================
PHYSICS_PROBLEMS = {
    "7": [
        {"question": "Автомобиль движется со скоростью 72 км/ч. Какой путь он пройдет за 10 секунд?", "options": ["200 м", "100 м", "300 м"], "correct": 0, "explanation": "72 км/ч = 20 м/с. S = v·t = 20·10 = 200 м."},
        {"question": "Какая сила тяжести действует на тело массой 5 кг? (g = 10 м/с²)", "options": ["50 Н", "10 Н", "5 Н"], "correct": 0, "explanation": "F = m·g = 5·10 = 50 Н."},
        {"question": "Лед плавает в воде. Какая часть льда находится над водой?", "options": ["1/9", "1/10", "1/11"], "correct": 1, "explanation": "ρ_лед ≈ 900 кг/м³, ρ_воды ≈ 1000 кг/м³. Над водой 1/10."},
        {"question": "Тело массой 2 кг падает свободно 5 с. С какой скоростью оно ударится о землю? (g=10 м/с²)", "options": ["25 м/с", "50 м/с", "10 м/с"], "correct": 1, "explanation": "v = g·t = 10·5 = 50 м/с."},
        {"question": "Какой объем займет 2 кг воды? (плотность воды 1000 кг/м³)", "options": ["0.002 м³", "2 м³", "2000 м³"], "correct": 0, "explanation": "V = m/ρ = 2/1000 = 0.002 м³."},
        {"question": "Сколько секунд в сутках?", "options": ["86400", "24000", "3600"], "correct": 0, "explanation": "24·60·60 = 86400 с."},
        {"question": "Какой вес имеет воздушный шар объемом 10 м³? (ρ_возд=1.2 кг/м³, g=10 м/с²)", "options": ["120 Н", "12 Н", "1.2 Н"], "correct": 0, "explanation": "m = 1.2·10 = 12 кг, P = m·g = 120 Н."},
        {"question": "Поезд идет 3 часа со скоростью 60 км/ч. Какое расстояние он прошел?", "options": ["180 км", "20 км", "300 км"], "correct": 0, "explanation": "S = v·t = 60·3 = 180 км."},
        {"question": "Какова плотность тела массой 5 кг и объемом 0.01 м³?", "options": ["500 кг/м³", "50 кг/м³", "0.05 кг/м³"], "correct": 0, "explanation": "ρ = m/V = 5/0.01 = 500 кг/м³."},
        {"question": "Чему равно ускорение свободного падения на Земле?", "options": ["9.8 м/с²", "10 м/с²", "3.6 м/с²"], "correct": 0, "explanation": "g ≈ 9.8 м/с² (или 10 м/с² для простоты)."},
        {"question": "Тело прошло путь 150 м за 30 с. Какова средняя скорость?", "options": ["5 м/с", "15 м/с", "0.2 м/с"], "correct": 0, "explanation": "v = S/t = 150/30 = 5 м/с."},
        {"question": "На тело действует сила 30 Н. За какое время она изменит скорость тела массой 3 кг с 0 до 10 м/с?", "options": ["1 с", "3 с", "10 с"], "correct": 0, "explanation": "a = F/m = 10 м/с², t = Δv/a = 10/10 = 1 с."}
    ],
    "8": [
        {"question": "Какое количество теплоты выделится при полном сгорании 2 кг каменного угля? (удельная теплота сгорания 30 МДж/кг)", "options": ["60 МДж", "30 МДж", "15 МДж"], "correct": 0, "explanation": "Q = m·q = 2·30 = 60 МДж."},
        {"question": "Сила тока в цепи 2 А, сопротивление 10 Ом. Какое напряжение?", "options": ["20 В", "5 В", "10 В"], "correct": 0, "explanation": "U = I·R = 2·10 = 20 В."},
        {"question": "Груз массой 10 кг поднимают на высоту 5 м. Какую работу совершают? (g = 10 м/с²)", "options": ["500 Дж", "50 Дж", "100 Дж"], "correct": 0, "explanation": "A = m·g·h = 10·10·5 = 500 Дж."},
        {"question": "Температура нагрелась с 20°C до 80°C. На сколько градусов изменилась температура?", "options": ["60°C", "100°C", "40°C"], "correct": 0, "explanation": "ΔT = 80−20 = 60°C."},
        {"question": "Мощность лампы 100 Вт, время работы 2 часа. Сколько энергии?", "options": ["0.72 МДж", "7.2 кДж", "720 Дж"], "correct": 0, "explanation": "A = P·t = 100·7200 = 720000 Дж = 0.72 МДж."},
        {"question": "Какое сопротивление у трех резисторов по 6 Ом, соединенных параллельно?", "options": ["2 Ом", "18 Ом", "6 Ом"], "correct": 0, "explanation": "1/R = 3/6 = 1/2 ⇒ R = 2 Ом."},
        {"question": "Сколько теплоты нужно для нагрева 1 кг воды на 1°C? (c=4200 Дж/(кг·°C))", "options": ["4200 Дж", "42 Дж", "420 Дж"], "correct": 0, "explanation": "Q = c·m·ΔT = 4200·1·1 = 4200 Дж."},
        {"question": "Мощность двигателя 5 кВт. Сколько работы за 10 мин?", "options": ["3 МДж", "0.3 МДж", "30 МДж"], "correct": 0, "explanation": "A = 5000·600 = 3·10⁶ Дж = 3 МДж."},
        {"question": "Два резистора 4 Ом и 6 Ом последовательно. Какое общее сопротивление?", "options": ["10 Ом", "2.4 Ом", "24 Ом"], "correct": 0, "explanation": "R = 4+6 = 10 Ом."},
        {"question": "Какая формула связи мощности, напряжения и тока?", "options": ["P = U·I", "P = U/R", "P = I/R"], "correct": 0, "explanation": "P = U·I."},
        {"question": "Сила тока 0.5 А течёт 10 минут. Какой заряд прошёл?", "options": ["300 Кл", "30 Кл", "3 Кл"], "correct": 0, "explanation": "q = I·t = 0.5·600 = 300 Кл."}
    ],
    "9": [
        {"question": "Тело брошено вверх со скоростью 20 м/с. Максимальная высота? (g = 10 м/с²)", "options": ["20 м", "10 м", "40 м"], "correct": 0, "explanation": "h = v²/(2g) = 400/20 = 20 м."},
        {"question": "Газ получает 100 Дж теплоты и совершает работу 60 Дж. Изменилась внутренняя энергия?", "options": ["+40 Дж", "-40 Дж", "+160 Дж"], "correct": 0, "explanation": "ΔU = Q−A = 100−60 = 40 Дж."},
        {"question": "Период маятника 2 с. Длина нити? (g = 9.8 м/с²)", "options": ["≈1 м", "≈2 м", "≈0.5 м"], "correct": 0, "explanation": "L ≈ (T²·g)/(4π²) ≈ 1 м."},
        {"question": "Автомобиль разгоняется от 0 до 20 м/с за 10 с. Ускорение?", "options": ["2 м/с²", "200 м/с²", "0.5 м/с²"], "correct": 0, "explanation": "a = Δv/Δt = 20/10 = 2 м/с²."},
        {"question": "Сила 50 Н на тело 10 кг. Ускорение?", "options": ["5 м/с²", "500 м/с²", "0.2 м/с²"], "correct": 0, "explanation": "a = F/m = 50/10 = 5 м/с²."},
        {"question": "Путь при равноускоренном движении? (v₀=0, a=2 м/с², t=5 с)", "options": ["25 м", "10 м", "50 м"], "correct": 0, "explanation": "S = at²/2 = 2·25/2 = 25 м."},
        {"question": "Мяч брошен под 30° со скоростью 20 м/с. Горизонтальная скорость?", "options": ["17.3 м/с", "10 м/с", "20 м/с"], "correct": 0, "explanation": "vx = v·cos30° ≈ 17.3 м/с."},
        {"question": "Импульс тела массой 2 кг и скоростью 5 м/с?", "options": ["10 кг·м/с", "7 кг·м/с", "2.5 кг·м/с"], "correct": 0, "explanation": "p = m·v = 2·5 = 10 кг·м/с."},
        {"question": "Газу сообщили 200 Дж теплоты, работа 50 Дж. Изменилась внутренняя энергия?", "options": ["+150 Дж", "+250 Дж", "-150 Дж"], "correct": 0, "explanation": "ΔU = 200−50 = 150 Дж."}
    ],
    "10": [
        {"question": "Протон в поле B=0.1 Тл, v=10⁶ м/с перпендикулярно. Сила? (q=1.6×10⁻¹⁹ Кл)", "options": ["1.6×10⁻¹⁴ Н", "3.2×10⁻¹⁴ Н", "8×10⁻¹⁵ Н"], "correct": 0, "explanation": "F = q·v·B = 1.6×10⁻¹⁴ Н."},
        {"question": "Фотон E=4×10⁻¹⁹ Дж. Длина волны? (h=6.63×10⁻³⁴, c=3×10⁸)", "options": ["≈500 нм", "≈250 нм", "≈750 нм"], "correct": 0, "explanation": "λ = hc/E ≈ 500 нм."},
        {"question": "²³⁵U + n → деление. Какая реакция?", "options": ["Деление", "Термоядерный синтез", "Распад"], "correct": 0, "explanation": "Реакция деления урана-235."},
        {"question": "Линза f=20 см. Расстояние предмета для действительного изображения?", "options": ["больше 20 см", "меньше 20 см", "ровно 20 см"], "correct": 0, "explanation": "d > f для действительного изображения."},
        {"question": "Частота 50 Гц, λ=2 м. Скорость волны?", "options": ["100 м/с", "25 м/с", "1 м/с"], "correct": 0, "explanation": "v = λ·ν = 2·50 = 100 м/с."},
        {"question": "C=10 мкФ, U=100 В. Заряд?", "options": ["0.001 Кл", "1 Кл", "0.1 Кл"], "correct": 0, "explanation": "Q = C·U = 10⁻³ Кл."},
        {"question": "Ток 2 А, 5 с. Заряд?", "options": ["10 Кл", "2.5 Кл", "7 Кл"], "correct": 0, "explanation": "q = I·t = 2·5 = 10 Кл."}
    ],
    "11": [
        {"question": "Провод L=1 м, v=5 м/с, B=0.1 Тл. ЭДС индукции?", "options": ["0.5 В", "0.05 В", "0.005 В"], "correct": 0, "explanation": "ε = B·v·L = 0.1·5·1 = 0.5 В."},
        {"question": "Δx=300 м, Δt=1 мкс. Характер интервала?", "options": ["Пространственный", "Временной", "Световой"], "correct": 2, "explanation": "cΔt = Δx ⇒ световой."},
        {"question": "Фотон 3 эВ. Частота? (h=4.14×10⁻¹⁵ эВ·с)", "options": ["7.25×10¹⁴ Гц", "7.25×10¹² Гц", "3×10¹⁴ Гц"], "correct": 0, "explanation": "ν = E/h ≈ 7.25×10¹⁴ Гц."},
        {"question": "Работа выхода 5 эВ. Скорость электронов?", "options": ["1.32×10⁶ м/с", "1.32×10⁵ м/с", "4×10⁶ м/с"], "correct": 0, "explanation": "v = √(2E/m) ≈ 1.32×10⁶ м/с."},
        {"question": "γ при v=0.8c?", "options": ["1.67", "1.25", "2"], "correct": 0, "explanation": "γ = 1/√(1−0.64) = 1.67."},
        {"question": "Энергия импульса лазера P=10⁹ Вт, t=10 нс?", "options": ["10 Дж", "10⁴ Дж", "0.01 Дж"], "correct": 0, "explanation": "E = P·t = 10⁹·10⁻⁸ = 10 Дж."},
        {"question": "Релятивистская масса при v=0.6c?", "options": ["1.25 раза", "1.67 раза", "2 раза"], "correct": 0, "explanation": "γ(0.6c) ≈ 1.25."}
    ]
}

# ============================================================================
# 4. БАЗА ОЛИМПИАД
# ============================================================================
OLYMPIADS = [
    {
        "name": "Всероссийская олимпиада школьников по физике",
        "description": "Главная государственная олимпиада по физике",
        "levels": ["7", "8", "9", "10", "11"],
        "importance": "Высшая",
        "registration_date": "Сентябрь-Октябрь 2026",
        "main_date": "Ноябрь 2026 — Март 2027",
        "url": "https://vserosolimp.edsoo.ru"
    },
    {
        "name": "Олимпиада «Ломоносов» (физика)",
        "description": "Олимпиада МГУ по физике для 7–11 классов",
        "levels": ["7", "8", "9", "10", "11"],
        "importance": "Высокая",
        "registration_date": "Октябрь-Ноябрь 2026",
        "main_date": "Декабрь 2026 — Февраль 2027",
        "url": "https://olimpiada.ru/activity/9"
    },
    {
        "name": "Олимпиада «Физтех»",
        "description": "Физико-техническая олимпиада МФТИ",
        "levels": ["8", "9", "10", "11"],
        "importance": "Высшая",
        "registration_date": "Октябрь-Ноябрь 2026",
        "main_date": "Декабрь 2026 — Март 2027",
        "url": "https://olymp-online.mipt.ru"
    },
    {
        "name": "Покори Воробьёвы горы! (физика)",
        "description": "Предметная олимпиада МГУ по физике",
        "levels": ["8", "9", "10", "11"],
        "importance": "Высокая",
        "registration_date": "Ноябрь-Декабрь 2026",
        "main_date": "Февраль 2027",
        "url": "https://olimpiada.ru/activity/166"
    },
    {
        "name": "Высшая проба ВШЭ (физика)",
        "description": "Олимпиада ВШЭ по физике для старших классов",
        "levels": ["10", "11"],
        "importance": "Высокая",
        "registration_date": "Ноябрь 2026",
        "main_date": "Февраль-Март 2027",
        "url": "https://olimpiada.ru/activity/42"
    },
    {
        "name": "Олимпиада Максвелла",
        "description": "Классическая олимпиада для 7–8 классов",
        "levels": ["7", "8"],
        "importance": "Высокая",
        "registration_date": "Декабрь 2026",
        "main_date": "Январь-Апрель 2027",
        "url": "https://maxwellspb.wordpress.com"
    },
    {
        "name": "Интернет-олимпиада по физике",
        "description": "Дистанционная олимпиада перечня",
        "levels": ["7", "8", "9", "10", "11"],
        "importance": "Высокая",
        "registration_date": "Октябрь-Ноябрь 2026",
        "main_date": "Ноябрь 2026 — Февраль 2027",
        "url": "https://www.ucheba.ru/for-abiturients/olympiads/physics"
    }
]

# ============================================================================
# 5. Система хранения состояния пользователей
# ============================================================================
user_data: Dict[int, Dict[str, Any]] = {}

# ============================================================================
# 6. Создание бота
# ============================================================================
async def create_bot_with_check():
    try:
        bot = Bot(token=BOT_TOKEN)
        me = await bot.get_me()
        logger.info(f"✅ Бот @{me.username} успешно авторизован!")
        logger.info(f"🆔 ID бота: {me.id}")
        return bot
    except TelegramUnauthorizedError:
        logger.error("❌ ОШИБКА АВТОРИЗАЦИИ! Токен недействителен.")
        raise

# ============================================================================
# 7. Диспетчер
# ============================================================================
dp = Dispatcher(storage=MemoryStorage())

# ============================================================================
# Вспомогательные функции для клавиатур
# ============================================================================
def get_main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Задачи по физике", callback_data="show_grades")],
        [InlineKeyboardButton(text="🏆 Олимпиады", callback_data="show_olympiads")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])

def get_olympiad_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Все", callback_data="olymp_all"), InlineKeyboardButton(text="7️⃣8️⃣", callback_data="olymp_78")],
        [InlineKeyboardButton(text="9️⃣🔟1️⃣1️⃣", callback_data="olymp_911"), InlineKeyboardButton(text="🏅 Престижные", callback_data="olymp_high")],
        [InlineKeyboardButton(text="📚 Задачи", callback_data="show_grades")]
    ])

# ============================================================================
# 8. КОМАНДЫ
# ============================================================================
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "🏆 Привет! Я бот-помощник по физике для подготовки к олимпиадам!\n\n"
        "📚 Выбери, что хочешь изучить:",
        reply_markup=get_main_menu_keyboard()
    )

@dp.message(Command("zadachi"))
async def cmd_zadachi(message: Message):
    await show_grade_selection(message)

@dp.message(Command("spisokolimpiad"))
async def cmd_olimpiads(message: Message):
    await show_olympiad_filters(message)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📚 <b>PhysicsBot v2.1</b>\n\n"
        "🎯 <b>Команды:</b>\n"
        "• /start - главное меню\n"
        "• /zadachi - задачи\n"
        "• /spisokolimpiad - олимпиады\n"
        "• /help - справка\n\n"
        "📖 <b>Задачи:</b> 7-11 классы, подробные объяснения\n"
        "🏅 <b>Олимпиады:</b> реальные олимпиады 2026-2027"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Задачи", callback_data="show_grades")],
        [InlineKeyboardButton(text="🏆 Олимпиады", callback_data="show_olympiads")]
    ])
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

# ============================================================================
# 9. ЗАДАЧИ
# ============================================================================
@dp.callback_query(F.data == "show_grades")
async def show_grade_selection_callback(callback: CallbackQuery):
    await show_grade_selection(callback.message)
    await callback.answer()

async def show_grade_selection(message_or_cb):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="7️⃣ 7 класс", callback_data="grade_7"), InlineKeyboardButton(text="8️⃣ 8 класс", callback_data="grade_8")],
        [InlineKeyboardButton(text="9️⃣ 9 класс", callback_data="grade_9"), InlineKeyboardButton(text="🔟 10 класс", callback_data="grade_10")],
        [InlineKeyboardButton(text="1️⃣1️⃣ 11 класс", callback_data="grade_11")]
    ])
    text = (
        "📚 <b>Выбери класс:</b>\n\n"
        "🟢 7 класс - механика\n"
        "🟡 8 класс - теплота, электричество\n"
        "🟠 9 класс - кинематика\n"
        "🔴 10 класс - электромагнетизм\n"
        "🟣 11 класс - СТО, квантовая физика"
    )
    if isinstance(message_or_cb, Message):
        await message_or_cb.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message_or_cb.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(F.data.startswith("grade_"))
async def send_problem(callback: CallbackQuery):
    grade = callback.data.split("_")[1]
    if grade not in PHYSICS_PROBLEMS:
        await callback.answer("Класс не найден!", show_alert=True)
        return

    problem = random.choice(PHYSICS_PROBLEMS[grade])
    user_data[callback.from_user.id] = {"problem": problem, "grade": grade}

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{i+1}. {option}", callback_data=f"answer_{i}_{grade}")]
        for i, option in enumerate(problem["options"])
    ])

    try:
        await callback.message.edit_text(
            f"📖 <b>{grade} класс</b>\n\n{problem['question']}\n\n<b>Ответ:</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        await callback.message.answer(
            f"📖 <b>{grade} класс</b>\n\n{problem['question']}\n\n<b>Ответ:</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    await callback.answer()

@dp.callback_query(F.data.startswith("answer_"))
async def check_answer(callback: CallbackQuery):
    parts = callback.data.split("_")
    user_answer = int(parts[1])
    grade = parts[2]

    user_id = callback.from_user.id
    problem = user_data.get(user_id, {}).get("problem")

    if not problem:
        await callback.answer("Сессия истекла! Выберите задачу заново.", show_alert=True)
        return

    correct = problem["correct"]

    if user_answer == correct:
        result = "✅ <b>ПРАВИЛЬНО!</b>"
        emoji = "🎉"
    else:
        result = f"❌ <b>НЕПРАВИЛЬНО!</b>\n<b>{correct+1}</b>. {problem['options'][correct]}"
        emoji = "😔"

    text = f"{emoji} {result}\n\n📝 <b>Решение:</b>\n{problem['explanation']}\n\n🔄 Ещё задачу?"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Ещё", callback_data=f"grade_{grade}"), InlineKeyboardButton(text="📚 Другой класс", callback_data="show_grades")],
        [InlineKeyboardButton(text="🏆 Олимпиады", callback_data="show_olympiads")]
    ])

    user_data.pop(user_id, None)

    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    await callback.answer()

# ============================================================================
# 10. ОЛИМПИАДЫ
# ============================================================================
@dp.callback_query(F.data == "show_olympiads")
async def show_olympiad_filters_callback(callback: CallbackQuery):
    await show_olympiad_filters(callback.message)
    await callback.answer()

async def show_olympiad_filters(message_or_cb):
    keyboard = get_olympiad_keyboard()
    current_year = datetime.now().year
    text = f"🏆 <b>Олимпиады {current_year}-{current_year+1}</b>\n\nВыбери категорию:"
    if isinstance(message_or_cb, Message):
        await message_or_cb.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message_or_cb.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(F.data.startswith("olymp_"))
async def show_olympiads(callback: CallbackQuery):
    category = callback.data.split("_")[1]
    current_year = datetime.now().year
    response = f"🏆 <b>Олимпиады {current_year}-{current_year+1}</b>\n\n"

    if category == "all":
        filtered = OLYMPIADS
        response += "📋 <b>Все олимпиады:</b>\n\n"
    elif category == "78":
        filtered = [o for o in OLYMPIADS if any(lvl in ["7", "8"] for lvl in o["levels"])]
        response += "🎯 <b>7-8 классы:</b>\n\n"
    elif category == "911":
        filtered = [o for o in OLYMPIADS if any(lvl in ["9", "10", "11"] for lvl in o["levels"])]
        response += "🎓 <b>9-11 классы:</b>\n\n"
    elif category == "high":
        filtered = [o for o in OLYMPIADS if o["importance"] in ["Высшая", "Высокая"]]
        response += "🏅 <b>Престижные:</b>\n\n"
    else:
        filtered = []

    if not filtered:
        response += "❌ Не найдено."
    else:
        for i, olymp in enumerate(filtered, 1):
            levels = ", ".join(olymp["levels"])
            response += (
                f"{i}. <b>{olymp['name']}</b>\n"
                f"   {olymp['description']}\n"
                f"   Классы: {levels}\n"
                f"   🏅 {olymp['importance']}\n"
                f"   📅 {olymp['registration_date']}\n"
                f"   📅 {olymp['main_date']}\n"
                f"   🔗 <a href='{olymp['url']}'>Сайт</a>\n\n"
            )

    try:
        await callback.message.edit_text(
            response,
            reply_markup=get_olympiad_keyboard(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except TelegramBadRequest:
        await callback.message.answer(
            response,
            reply_markup=get_olympiad_keyboard(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )

    await callback.answer()

@dp.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    text = (
        "📚 <b>PhysicsBot v2.1</b>\n\n"
        "🎯 <b>Команды:</b>\n"
        "• /start - главное меню\n"
        "• /zadachi - задачи\n"
        "• /spisokolimpiad - олимпиады\n"
        "• /help - справка\n\n"
        "📖 <b>Задачи:</b> 7-11 классы, подробные объяснения\n"
        "🏅 <b>Олимпиады:</b> реальные олимпиады 2026-2027"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Задачи", callback_data="show_grades")],
        [InlineKeyboardButton(text="🏆 Олимпиады", callback_data="show_olympiads")]
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# ============================================================================
# 11. ЗАПУСК
# ============================================================================
async def main():
    logger.info("=" * 50)
    logger.info("🚀 PHYSICS BOT v2.1")
    logger.info("=" * 50)
    logger.info(f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    logger.info("=" * 50)

    bot = None
    try:
        bot = await create_bot_with_check()
        logger.info("✅ Бот готов! Команды: /start, /zadachi, /spisokolimpiad")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("👋 Остановлен пользователем (KeyboardInterrupt)")
    except Exception as e:
        logger.exception(f"❌ Необработанная ошибка: {e}")
    finally:
        if bot:
            await bot.session.close()
            logger.info("🔌 Сессия бота закрыта")

if __name__ == "__main__":
    asyncio.run(main())
