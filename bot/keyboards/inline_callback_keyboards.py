from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_single_choice_kb(choices: list, callback_prefix):
    buttons = [[InlineKeyboardButton(text=f'{choice}', callback_data=f"{callback_prefix}_{i}")] for i, choice in enumerate(choices)]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def cmd_inline_btn(commands : list[str,str]):
    buttons = [[InlineKeyboardButton(text=f'{text}', callback_data=f"{callback}")] for text, callback in commands]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard