"""
PHYSICS BOT - Telegram бот для изучения физики и подготовки к олимпиадам
Автор: Жаворонков Ярослав Николаевич, 7Д класс
Руководитель: Жаворонков Николай Валерьевич, ИТ-директор сети магазинов "О КЕЙ"
Версия: 2.0 (aiogram)
Дата: 2026 год
"""

import logging
import random
import asyncio
from datetime import datetime
from typing import Dict, Any
import json
from pathlib import Path
import re
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramUnauthorizedError

# ============================================================================
# 1. НАСТРОЙКА ЛОГИРОВАНИЯ
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# 2. ТОКЕН БОТА (НОВЫЙ ТОКЕН)
# ============================================================================
# BOT_TOKEN = "8508332502:AAExc3wGBcwMb8nMxQtWL-DJVEvjhIvcQ40"

BOT_TOKEN = os.getenv('BOT_TOKEN')
if BOT_TOKEN is None:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена!")
    
def validate_token(token):
    """Проверяет формат токена Telegram"""
    pattern = r'^\d+:[a-zA-Z0-9_-]+$'
    if re.match(pattern, token):
        logger.info("✅ Формат токена правильный")
        return True
    else:
        logger.error("❌ Неверный формат токена!")
        return False

# Проверяем токен перед запуском
if not validate_token(BOT_TOKEN):
    print("❌ ОШИБКА: Неверный формат токена!")
    print("Токен должен быть в формате: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz")
    print("Проверьте токен в BotFather и обновите его в коде")
    exit(1)

# ============================================================================
# 3. ПОЛНАЯ БАЗА ДАННЫХ ЗАДАЧ ПО ФИЗИКЕ (7-11 КЛАССЫ)
# ============================================================================
PHYSICS_PROBLEMS = {
    "7": [
        {
            "question": "Автомобиль движется со скоростью 72 км/ч. Какой путь он пройдет за 10 секунд?",
            "options": ["200 м", "100 м", "300 м"],
            "correct": 0,
            "explanation": "Сначала переведем скорость в м/с: 72 км/ч = 72 * 1000 / 3600 = 20 м/с. Затем путь S = v * t = 20 * 10 = 200 м."
        },
        {
            "question": "Какая сила тяжести действует на тело массой 5 кг? (g = 10 м/с²)",
            "options": ["50 Н", "10 Н", "5 Н"],
            "correct": 0,
            "explanation": "Сила тяжести F = m * g = 5 * 10 = 50 Н."
        },
        {
            "question": "Лед плавает в воде. Какая часть льда находится над водой?",
            "options": ["1/9", "1/10", "1/11"],
            "correct": 2,
            "explanation": "По закону Архимеда, объем погруженной части равен отношению плотности льда (900 кг/м³) к плотности воды (1000 кг/м³). Над водой остается 1 - 900/1000 = 1/10."
        },
        {
            "question": "Тело массой 2 кг падает свободно 5 с. С какой скоростью оно ударится о землю? (g=10 м/с²)",
            "options": ["25 м/с", "50 м/с", "10 м/с"],
            "correct": 1,
            "explanation": "v = g*t = 10*5 = 50 м/с."
        },
        {
            "question": "Какой объем займет 2 кг воды? (плотность воды 1000 кг/м³)",
            "options": ["0.002 м³", "2 м³", "2000 м³"],
            "correct": 0,
            "explanation": "V = m/ρ = 2/1000 = 0.002 м³ = 2 л."
        },
        {
            "question": "Сколько секунд в сутках?",
            "options": ["86400", "24000", "3600"],
            "correct": 0,
            "explanation": "24ч*60мин*60с = 86400 с."
        },
        {
            "question": "Какой вес имеет воздушный шар объемом 10 м³? (ρ_возд=1.2 кг/м³)",
            "options": ["12 кг", "1.2 кг", "120 кг"],
            "correct": 0,
            "explanation": "m = ρ*V = 1.2*10 = 12 кг."
        },
        {
            "question": "Поезд идет 3 часа со скоростью 60 км/ч. Какое расстояние он прошел?",
            "options": ["180 км", "20 км", "300 км"],
            "correct": 0,
            "explanation": "S = v*t = 60*3 = 180 км."
        },
        {
            "question": "Какова плотность тела массой 5 кг и объемом 0.01 м³?",
            "options": ["500 кг/м³", "50 кг/м³", "0.05 кг/м³"],
            "correct": 0,
            "explanation": "ρ = m/V = 5/0.01 = 500 кг/м³."
        },
        {
            "question": "Чему равна ускорение свободного падения на Земле?",
            "options": ["9.8 м/с²", "10 м/с²", "3.6 м/с²"],
            "correct": 0,
            "explanation": "g ≈ 9.8 м/с² (принимают 10 м/с² для упрощения расчетов)."
        }
    ],
    "8": [
        {
            "question": "Какое количество теплоты выделится при полном сгорании 2 кг каменного угля? (удельная теплота сгорания 30 МДж/кг)",
            "options": ["60 МДж", "30 МДж", "15 МДж"],
            "correct": 0,
            "explanation": "Q = m * q = 2 * 30 = 60 МДж."
        },
        {
            "question": "Сила тока в цепи 2 А, сопротивление 10 Ом. Какое напряжение на концах проводника?",
            "options": ["20 В", "5 В", "10 В"],
            "correct": 0,
            "explanation": "По закону Ома: U = I * R = 2 * 10 = 20 В."
        },
        {
            "question": "Груз массой 10 кг поднимают на высоту 5 м. Какую работу при этом совершают? (g = 10 м/с²)",
            "options": ["500 Дж", "50 Дж", "100 Дж"],
            "correct": 0,
            "explanation": "A = m * g * h = 10 * 10 * 5 = 500 Дж."
        },
        {
            "question": "Температура нагрелась с 20°C до 80°C. На сколько градусов изменилась температура?",
            "options": ["60°C", "100°C", "40°C"],
            "correct": 0,
            "explanation": "ΔT = T₂ - T₁ = 80 - 20 = 60°C."
        },
        {
            "question": "Мощность лампы 100 Вт, время работы 2 часа. Сколько энергии она израсходовала?",
            "options": ["0.72 МДж", "7.2 кДж", "720 Дж"],
            "correct": 0,
            "explanation": "A = P*t = 100*7200 = 720000 Дж = 0.72 МДж."
        },
        {
            "question": "Какое сопротивление у трех резисторов по 6 Ом, соединенных параллельно?",
            "options": ["2 Ом", "18 Ом", "6 Ом"],
            "correct": 0,
            "explanation": "1/R = 1/6 + 1/6 + 1/6 = 3/6 = 1/2 => R = 2 Ом."
        },
        {
            "question": "Сколько теплоты нужно для нагрева 1 кг воды на 1°C? (c=4200 Дж/(кг·°C))",
            "options": ["4200 Дж", "42 Дж", "420 Дж"],
            "correct": 0,
            "explanation": "Q = c*m*ΔT = 4200*1*1 = 4200 Дж."
        },
        {
            "question": "Мощность двигателя 5 кВт. Сколько работы он совершит за 10 мин?",
            "options": ["3 МДж", "0.3 МДж", "30 МДж"],
            "correct": 0,
            "explanation": "A = P*t = 5000*600 = 3 000 000 Дж = 3 МДж."
        },
        {
            "question": "Два резистора 4 Ом и 6 Ом соединены последовательно. Какое общее сопротивление?",
            "options": ["10 Ом", "2.4 Ом", "24 Ом"],
            "correct": 0,
            "explanation": "R = R₁ + R₂ = 4 + 6 = 10 Ом."
        },
        {
            "question": "Какая формула связи мощности, напряжения и тока?",
            "options": ["P = U*I", "P = U/R", "P = I/R"],
            "correct": 0,
            "explanation": "P = U*I - основная формула мощности."
        }
    ],
    "9": [
        {
            "question": "Тело брошено вертикально вверх со скоростью 20 м/с. На какую максимальную высоту оно поднимется? (g = 10 м/с²)",
            "options": ["20 м", "10 м", "40 м"],
            "correct": 0,
            "explanation": "h = v² / (2g) = 400 / 20 = 20 м."
        },
        {
            "question": "Идеальный газ получает 100 Дж теплоты и совершает работу 60 Дж. Как изменилась его внутренняя энергия?",
            "options": ["Увеличилась на 40 Дж", "Уменьшилась на 40 Дж", "Увеличилась на 160 Дж"],
            "correct": 0,
            "explanation": "По первому закону термодинамики: ΔU = Q - A = 100 - 60 = 40 Дж."
        },
        {
            "question": "Период колебаний математического маятника 2 с. Какова длина нити? (g = 9.8 м/с²)",
            "options": ["≈1 м", "≈2 м", "≈0.5 м"],
            "correct": 0,
            "explanation": "T = 2π√(L/g) => L = (T² * g) / (4π²) = (4 * 9.8) / (4 * 9.87) ≈ 1 м."
        },
        {
            "question": "Автомобиль разгонается от 0 до 20 м/с за 10 с. Какое ускорение?",
            "options": ["2 м/с²", "200 м/с²", "0.5 м/с²"],
            "correct": 0,
            "explanation": "a = Δv/Δt = 20/10 = 2 м/с²."
        },
        {
            "question": "Сила 50 Н действует на тело массой 10 кг. Какое ускорение получится?",
            "options": ["5 м/с²", "500 м/с²", "0.2 м/с²"],
            "correct": 0,
            "explanation": "a = F/m = 50/10 = 5 м/с²."
        },
        {
            "question": "Какой путь пройдет тело при равноускоренном движении? (v₀=0, a=2 м/с², t=5 с)",
            "options": ["25 м", "10 м", "50 м"],
            "correct": 0,
            "explanation": "S = v₀t + at²/2 = 0 + 2*25/2 = 25 м."
        },
        {
            "question": "Мяч брошен под углом 30° со скоростью 20 м/с. Какова горизонтальная составляющая скорости? (g=10 м/с²)",
            "options": ["17.3 м/с", "10 м/с", "20 м/с"],
            "correct": 0,
            "explanation": "vx = v₀*cosα = 20*cos30° = 20*(√3/2) ≈ 17.3 м/с."
        },
        {
            "question": "Какой импульс имеет тело массой 2 кг и скоростью 5 м/с?",
            "options": ["10 кг·м/с", "7 кг·м/с", "2.5 кг·м/с"],
            "correct": 0,
            "explanation": "p = m*v = 2*5 = 10 кг·м/с."
        }
    ],
    "10": [
        {
            "question": "Протон движется в магнитном поле с индукцией 0.1 Тл со скоростью 10⁶ м/с перпендикулярно линиям индукции. Какая сила действует на протон? (заряд протона 1.6×10⁻¹⁹ Кл)",
            "options": ["1.6×10⁻¹⁴ Н", "3.2×10⁻¹⁴ Н", "8×10⁻¹⁵ Н"],
            "correct": 0,
            "explanation": "F = q * v * B * sinα = 1.6×10⁻¹⁹ * 10⁶ * 0.1 * 1 = 1.6×10⁻¹⁴ Н."
        },
        {
            "question": "Фотон имеет энергию 4×10⁻¹⁹ Дж. Какова длина волны этого фотона? (h = 6.63×10⁻³⁴ Дж·с, c = 3×10⁸ м/с)",
            "options": ["≈500 нм", "≈250 нм", "≈750 нм"],
            "correct": 0,
            "explanation": "λ = h * c / E = (6.63×10⁻³⁴ * 3×10⁸) / 4×10⁻¹⁹ ≈ 5×10⁻⁷ м = 500 нм."
        },
        {
            "question": "Ядро урана ²³⁵U захватывает нейтрон и делится на два осколка и 2 нейтрона. Какая реакция происходит?",
            "options": ["Ядерная реакция деления", "Термоядерная реакция", "Радиоактивный распад"],
            "correct": 0,
            "explanation": "Это типичная реакция деления ядра урана-235."
        },
        {
            "question": "Линза фокусного расстояния 20 см. На каком расстоянии от линзы расположить предмет для получения действительного изображения?",
            "options": ["больше 20 см", "меньше 20 см", "ровно 20 см"],
            "correct": 0,
            "explanation": "Для действительного изображения предмет должен быть дальше фокуса (d > f)."
        },
        {
            "question": "Частота волны 50 Гц, длина волны 2 м. Какова скорость распространения?",
            "options": ["100 м/с", "25 м/с", "1 м/с"],
            "correct": 0,
            "explanation": "v = λ*f = 2*50 = 100 м/с."
        },
        {
            "question": "Емкость конденсатора 10 мкФ, напряжение 100 В. Какой заряд?",
            "options": ["0.001 Кл", "1 Кл", "0.1 Кл"],
            "correct": 0,
            "explanation": "Q = C*U = 10×10⁻⁶*100 = 0.001 Кл = 1 мКл."
        },
        {
            "question": "Ток 2 А течет 5 с. Какой заряд прошел?",
            "options": ["10 Кл", "2.5 Кл", "7 Кл"],
            "correct": 0,
            "explanation": "q = I*t = 2*5 = 10 Кл."
        }
    ],
    "11": [
        {
            "question": "По проводу длиной 1 м движется со скоростью 5 м/с перпендикулярно линиям индукции магнитного поля (В=0.1 Тл). Какая ЭДС индукции возникает в проводе?",
            "options": ["0.5 В", "0.05 В", "0.005 В"],
            "correct": 0,
            "explanation": "ЭДС индукции в движущемся проводнике: ε = B * v * L * sinα = 0.1 * 5 * 1 * 1 = 0.5 В."
        },
        {
            "question": "В СТО два события разделены интервалом Δx=300 м, Δt=1 мкс. Какой характер интервала?",
            "options": ["Пространственный", "Временной", "Световой"],
            "correct": 2,
            "explanation": "cΔt = 3×10⁸*10⁻⁶ = 300 м = Δx. Это световой интервал."
        },
        {
            "question": "Энергия фотона 3 эВ. Какова частота? (h=4.14×10⁻¹⁵ эВ·с)",
            "options": ["7.25×10¹⁴ Гц", "7.25×10¹² Гц", "3×10¹⁴ Гц"],
            "correct": 0,
            "explanation": "ν = E/h = 3/(4.14×10⁻¹⁵) ≈ 7.25×10¹⁴ Гц."
        },
        {
            "question": "Работа выхода электрона 5 эВ. Какова скорость электронов при фотоэффекте? (m_e=9.1×10⁻³¹ кг)",
            "options": ["1.32×10⁶ м/с", "1.32×10⁵ м/с", "4×10⁶ м/с"],
            "correct": 0,
            "explanation": "E = mv²/2 => v = √(2E/m) ≈ 1.32×10⁶ м/с."
        },
        {
            "question": "Релятивистский фактор Лоренца при v=0.8c равен?",
            "options": ["1.67", "1.25", "2"],
            "correct": 0,
            "explanation": "γ = 1/√(1-v²/c²) = 1/√(1-0.64) = 1/√0.36 = 1/0.6 = 1.67."
        },
        {
            "question": "Энергия связи нуклона в ядре ≈8 МэВ. Сколько энергии выделится при делении 1 кг урана-235?",
            "options": ["≈6.8×10¹³ Дж", "≈8×10¹¹ Дж", "≈10¹⁵ Дж"],
            "correct": 0,
            "explanation": "N≈2.5×10²³ нуклонов, E≈2×10¹³ Дж ≈ 6.8×10¹³ Дж."
        },
        {
            "question": "В импульсном режиме лазера мощность 10⁹ Вт, длительность 10 нс. Какая энергия импульса?",
            "options": ["10 Дж", "10⁴ Дж", "0.01 Дж"],
            "correct": 0,
            "explanation": "E = P*t = 10⁹*10⁻⁸ = 10 Дж."
        },
        {
            "question": "Длина волны де Бройля электрона с энергией 100 эВ?",
            "options": ["0.122 нм", "1.22 нм", "12.2 нм"],
            "correct": 0,
            "explanation": "λ = h/√(2mE) ≈ 0.122 нм."
        },
        {
            "question": "В СТО время собственного промежутка τ=1 мкс. При скорости 0.6c каково время в лабораторной системе?",
            "options": ["1.25 мкс", "0.8 мкс", "1.67 мкс"],
            "correct": 0,
            "explanation": "Δt = γτ = 1.25*1 = 1.25 мкс."
        },
        {
            "question": "Постоянная тонкой структуры α≈1/137. Чему равна скорость электрона в первом орбитале атома водорода?",
            "options": ["c/137", "c/100", "0.01c"],
            "correct": 0,
            "explanation": "v₁ = αc ≈ c/137."
        }
    ]
}

# ============================================================================
# ПОЛНАЯ БАЗА ОЛИМПИАД (обновленные ссылки)
# ============================================================================
OLYMPIADS = [
    {
        "name": "Всероссийская олимпиада школьников по физике",
        "description": "Самая престижная школьная олимпиада",
        "levels": ["9", "10", "11"],
        "importance": "Высшая",
        "registration_date": "Сентябрь-Октябрь 2026",
        "main_date": "Январь-Март 2027",
        "url": "https://olimpiada.ru/activity/74"  # профиль ВОШ по физике [web:20]
    },
    {
        "name": "Олимпиада Ломоносова МГУ",
        "description": "Физический тур МГУ и МФТИ",
        "levels": ["8", "9", "10", "11"],
        "importance": "Высокая",
        "registration_date": "Октябрь-Ноябрь 2026",
        "main_date": "Январь 2027",
        "url": "https://olimpiada.ru/activity/9"  # профиль Ломоносов по физике [web:1]
    },
    {
        "name": "Олимпиада Высшая проба ВШЭ",
        "description": "Физика для старших классов",
        "levels": ["10", "11"],
        "importance": "Высокая",
        "registration_date": "Ноябрь 2026",
        "main_date": "Февраль 2027",
        "url": "https://olimpiada.ru/activity/42"  # профиль Высшая проба по физике [web:1]
    },
    {
        "name": "Физтех МФТИ",
        "description": "Олимпиада МФТИ по физике",
        "levels": ["9", "10", "11"],
        "importance": "Высшая",
        "registration_date": "Ноябрь 2026",
        "main_date": "Февраль-Март 2027",
        "url": "https://olymp-online.mipt.ru"  # официальный сайт олимпиады «Физтех» [web:12][web:18]
    },
    {
        "name": "Покори Воробьёвы горы! МГУ",
        "description": "Олимпиада МГУ по физике",
        "levels": ["8", "9", "10", "11"],
        "importance": "Высокая",
        "registration_date": "Декабрь 2026",
        "main_date": "Февраль 2027",
        "url": "https://olimpiada.ru/activity/166"  # профиль «Покори Воробьёвы горы!» по физике [web:5]
    },
    {
        "name": "Олимпиада по физике для 7-8 классов",
        "description": "Всероссийская олимпиада младших школьников",
        "levels": ["7", "8"],
        "importance": "Первая",
        "registration_date": "Октябрь 2026",
        "main_date": "Декабрь 2026",
        "url": "https://www.ucheba.ru/for-abiturients/olympiads/physics"  # сводная страница олимпиад по физике [web:4]
    },
    {
        "name": "Инженерная олимпиада ОКей",
        "description": "Олимпиада от сети О КЕЙ",
        "levels": ["7", "8", "9"],
        "importance": "Вторая",
        "registration_date": "Ноябрь 2026",
        "main_date": "Январь 2027",
        "url": "https://okey.ru"  # основной сайт сети (под олимпиаду можно сделать раздел)
    },
    {
        "name": "Олимпиада Росатома",
        "description": "Атомная энергия в спорте",
        "levels": ["9", "10", "11"],
        "importance": "Высокая",
        "registration_date": "Октябрь 2026",
        "main_date": "Март 2027",
        "url": "https://olimpiada.ru/activity/100"  # профиль олимпиады Росатома [web:7]
    }
]


# ============================================================================
# 4. Состояния FSM
# ============================================================================
class PhysicsBotStates(StatesGroup):
    waiting_for_grade = State()
    waiting_for_answer = State()
    olympiad_filter = State()


# ============================================================================
# 5. Хранение состояния пользователей
# ============================================================================
user_data: Dict[int, Dict[str, Any]] = {}

# ============================================================================
# 6. Функция для создания бота с проверкой
# ============================================================================
async def create_bot_with_check():
    """Создает бота и проверяет токен"""
    try:
        bot = Bot(token=BOT_TOKEN)
        # Проверяем токен, получая информацию о боте
        me = await bot.get_me()
        logger.info(f"✅ Бот @{me.username} успешно авторизован!")
        logger.info(f"🆔 ID бота: {me.id}")
        logger.info(f"📝 Имя бота: {me.full_name}")
        return bot
    except TelegramUnauthorizedError:
        logger.error("❌ Ошибка авторизации: Неверный токен!")
        print("\n" + "="*50)
        print("❌ ОШИБКА АВТОРИЗАЦИИ!")
        print("="*50)
        print("Токен бота недействителен. Возможные причины:")
        print("1. Токен был сброшен в BotFather")
        print("2. Токен скопирован неправильно")
        print("3. Бот был удален")
        print("\nРешение:")
        print("1. Откройте Telegram")
        print("2. Найдите @BotFather")
        print("3. Отправьте /mybots")
        print("4. Выберите своего бота")
        print("5. Нажмите 'API Token'")
        print("6. Скопируйте новый токен")
        print("7. Замените токен в коде")
        print("="*50)
        raise
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка при создании бота: {e}")
        raise

# ============================================================================
# 7. Инициализация диспетчера
# ============================================================================
dp = Dispatcher(storage=MemoryStorage())


# ============================================================================
# 8. ОБРАБОТЧИКИ КОМАНД
# ============================================================================

@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Задачи по физике", callback_data="show_grades")],
        [InlineKeyboardButton(text="🏆 Олимпиады", callback_data="show_olympiads")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])

    await message.answer(
        "🏆 Привет! Я бот-помощник по физике для подготовки к олимпиадам!\n\n"
        "📚 Выбери что хочешь изучить:",
        reply_markup=keyboard
    )


@dp.message(Command("zadachi"))
async def cmd_zadachi(message: Message):
    """Команда /zadachi - выбор класса"""
    await show_grade_selection(message)


@dp.message(Command("spisokolimpiad"))
async def cmd_olimpiads(message: Message):
    """Команда /spisokolimpiad - фильтр олимпиад"""
    await show_olympiad_filters(message)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help"""
    text = (
        "📚 <b>Помощь по боту PhysicsBot</b>\n\n"
        "🎯 <b>Команды:</b>\n"
        "• /start - главное меню\n"
        "• /zadachi - задачи по физике\n"
        "• /spisokolimpiad - олимпиады\n"
        "• /help - эта справка\n\n"
        "📖 <b>Как решать задачи:</b>\n"
        "1. Нажми /zadachi\n"
        "2. Выбери класс (7-11)\n"
        "3. Выбери ответ\n"
        "4. Получи объяснение!\n\n"
        "🏅 <b>Олимпиады:</b>\n"
        "Получи актуальную информацию о всех олимпиадах!"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Задачи", callback_data="show_grades")],
        [InlineKeyboardButton(text="🏆 Олимпиады", callback_data="show_olympiads")]
    ])

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# ============================================================================
# 9. CALLBACK ОБРАБОТЧИКИ
# ============================================================================

@dp.callback_query(F.data == "show_grades")
async def show_grade_selection_callback(callback: CallbackQuery):
    """Показать выбор класса"""
    await show_grade_selection(callback.message)
    await callback.answer()


async def show_grade_selection(message_or_cb):
    """Показать клавиатуру выбора класса"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="7️⃣ 7 класс", callback_data="grade_7"),
            InlineKeyboardButton(text="8️⃣ 8 класс", callback_data="grade_8")
        ],
        [
            InlineKeyboardButton(text="9️⃣ 9 класс", callback_data="grade_9"),
            InlineKeyboardButton(text="🔟 10 класс", callback_data="grade_10")
        ],
        [
            InlineKeyboardButton(text="1️⃣1️⃣ 11 класс", callback_data="grade_11")
        ]
    ])

    text = (
        "📚 <b>Выбери класс для получения задачи:</b>\n\n"
        "🟢 7 класс - механика\n"
        "🟡 8 класс - теплота, электричество\n"
        "🟠 9 класс - кинематика, термодинамика\n"
        "🔴 10 класс - электромагнетизм, оптика\n"
        "🟣 11 класс - СТО, квантовая физика"
    )

    if isinstance(message_or_cb, Message):
        await message_or_cb.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message_or_cb.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@dp.callback_query(F.data.startswith("grade_"))
async def send_problem(callback: CallbackQuery):
    """Отправить задачу выбранного класса"""
    grade = callback.data.split("_")[1]

    if grade not in PHYSICS_PROBLEMS:
        await callback.answer("Класс не найден!", show_alert=True)
        return

    # Сохраняем задачу для пользователя
    problem = random.choice(PHYSICS_PROBLEMS[grade])
    user_data[callback.from_user.id] = {
        "problem": problem,
        "grade": grade
    }

    # Создаем кнопки ответов
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{i + 1}. {option}",
            callback_data=f"answer_{i}_{grade}"
        )] for i, option in enumerate(problem["options"])
    ])

    await callback.message.edit_text(
        f"📖 <b>Задача для {grade} класса</b>\n\n"
        f"{problem['question']}\n\n"
        f"<b>Выбери правильный ответ:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("answer_"))
async def check_answer(callback: CallbackQuery):
    """Проверить ответ пользователя"""
    parts = callback.data.split("_")
    user_answer = int(parts[1])
    grade = parts[2]

    user_id = callback.from_user.id
    if user_id not in user_data:
        await callback.answer("Сессия истекла. Выбери новую задачу!", show_alert=True)
        return

    problem = user_data[user_id]["problem"]
    correct_answer = problem["correct"]

    is_correct = (user_answer == correct_answer)

    if is_correct:
        result = "✅ <b>ПРАВИЛЬНО!</b>"
        emoji = "🎉"
    else:
        result = f"❌ <b>НЕПРАВИЛЬНО!</b>\nПравильный ответ: <b>{correct_answer + 1}</b>. {problem['options'][correct_answer]}"
        emoji = "😔"

    text = (
        f"{emoji} {result}\n\n"
        f"📝 <b>Объяснение решения:</b>\n"
        f"{problem['explanation']}\n\n"
        f"🔄 Хочешь еще одну задачу?"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Еще одну", callback_data=f"grade_{grade}"),
            InlineKeyboardButton(text="📚 Другой класс", callback_data="show_grades")
        ],
        [InlineKeyboardButton(text="🏆 Олимпиады", callback_data="show_olympiads")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Обработчики олимпиад
@dp.callback_query(F.data == "show_olympiads")
async def show_olympiad_filters_callback(callback: CallbackQuery):
    """Показать фильтры олимпиад"""
    await show_olympiad_filters(callback.message)
    await callback.answer()


async def show_olympiad_filters(message_or_cb):
    """Клавиатура фильтров олимпиад"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Все олимпиады", callback_data="olymp_all"),
            InlineKeyboardButton(text="7️⃣8️⃣ 7-8 класс", callback_data="olymp_78")
        ],
        [
            InlineKeyboardButton(text="9️⃣🔟1️⃣1️⃣ 9-11 класс", callback_data="olymp_911"),
            InlineKeyboardButton(text="🏅 Высший уровень", callback_data="olymp_high")
        ]
    ])

    current_year = datetime.now().year
    text = (
        f"🏆 <b>Актуальные олимпиады {current_year}-{current_year + 1}</b>\n\n"
        "Выбери категорию:"
    )

    if isinstance(message_or_cb, Message):
        await message_or_cb.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message_or_cb.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@dp.callback_query(F.data.startswith("olymp_"))
async def show_olympiads(callback: CallbackQuery):
    """Показать отфильтрованные олимпиады"""
    category = callback.data.split("_")[1]

    current_year = datetime.now().year
    response = f"🏆 <b>Олимпиады по физике {current_year}-{current_year + 1}</b>\n\n"

    filtered_olympiads = []

    if category == "all":
        filtered_olympiads = OLYMPIADS
        response += "📋 <b>Все олимпиады</b>:\n\n"
    elif category == "78":
        filtered_olympiads = [o for o in OLYMPIADS if "7" in o["levels"] or "8" in o["levels"]]
        response += "🎯 <b>Для 7-8 классов</b>:\n\n"
    elif category == "911":
        filtered_olympiads = [o for o in OLYMPIADS if any(lvl in ["9", "10", "11"] for lvl in o["levels"])]
        response += "🎓 <b>Для 9-11 классов</b>:\n\n"
    elif category == "high":
        filtered_olympiads = [o for o in OLYMPIADS if o["importance"] in ["Высшая", "Высокая"]]
        response += "🏅 <b>Самые престижные</b>:\n\n"

    if not filtered_olympiads:
        response += "❌ Олимпиады не найдены для этой категории."
    else:
        for i, olymp in enumerate(filtered_olympiads, 1):
            levels = ", ".join(olymp["levels"])
            response += (
                f"{i}. <b>{olymp['name']}</b>\n"
                f"   📝 {olymp['description']}\n"
                f"   🎯 Классы: {levels}\n"
                f"   🏅 Уровень: <b>{olymp['importance']}</b>\n"
                f"   📅 Регистрация: {olymp['registration_date']}\n"
                f"   📅 Тур: {olymp['main_date']}\n"
                f"   🔗 <a href='{olymp['url']}'>Сайт олимпиады</a>\n\n"
            )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Все", callback_data="olymp_all"),
            InlineKeyboardButton(text="7️⃣8️⃣", callback_data="olymp_78")
        ],
        [
            InlineKeyboardButton(text="9️⃣🔟1️⃣1️⃣", callback_data="olymp_911"),
            InlineKeyboardButton(text="🏅 Престижные", callback_data="olymp_high")
        ],
        [InlineKeyboardButton(text="📚 Задачи", callback_data="show_grades")]
    ])

    await callback.message.edit_text(response, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()


@dp.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    """Callback для помощи"""
    await cmd_help(callback.message)
    await callback.answer()


# ============================================================================
# 10. ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА
# ============================================================================
async def main():
    """Запуск бота с проверкой"""
    print("\n" + "="*50)
    print("🚀 PHYSICS BOT v2.0")
    print("="*50)
    print(f"📅 Дата запуска: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print("="*50)
    
    bot = None
    try:
        # Создаем бота с проверкой токена
        bot = await create_bot_with_check()
        
        print("\n📱 Доступные команды:")
        print("   /start - главное меню")
        print("   /zadachi - задачи по физике")
        print("   /spisokolimpiad - список олимпиад")
        print("   /help - помощь")
        print("\n" + "="*50)
        print("✅ Бот готов к работе!")
        print("⏳ Ожидание сообщений...")
        print("="*50 + "\n")
        
        # Запускаем поллинг
        await dp.start_polling(bot)
        
    except TelegramUnauthorizedError:
        # Ошибка уже обработана в create_bot_with_check
        pass
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        print(f"\n❌ Произошла ошибка: {e}")
    finally:
        if bot:
            await bot.session.close()
            print("🔌 Сессия бота закрыта")
            print("👋 Программа завершена")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Программа завершена")
    except Exception as e:
        print(f"\n❌ Необработанная ошибка: {e}")
