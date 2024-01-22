from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_yes_no_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="Да")
    kb.button(text="Нет")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def get_single_choice_kb(choices: list, callback_prefix):
    buttons = [[InlineKeyboardButton(text=f'{choice}', callback_data=f"{callback_prefix}_{i}")] for i, choice in enumerate(choices)]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard