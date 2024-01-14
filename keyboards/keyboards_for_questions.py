from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_yes_no_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="Да")
    kb.button(text="Нет")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def get_single_choice_kb(choices: list) -> ReplyKeyboardMarkup:
    # markup = InlineKeyboardMarkup()
    # markup.add(InlineKeyboardButton('🇺🇸 English', callback_data='lang_en'))
    # markup.add(InlineKeyboardButton('🇷🇺 Русский', callback_data='lang_ru'))
    # markup.add(InlineKeyboardButton('🇺🇦 Українська', callback_data='lang_uk'))
    # Предполагается, что choices - это список строк с вариантами выбора
    buttons = [KeyboardButton(text=choice) for choice in choices]
    
    # Создание клавиатуры с одной колонкой
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(*buttons)
    
    return kb