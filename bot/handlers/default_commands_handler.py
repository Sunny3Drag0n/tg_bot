from aiogram import  Router, F
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    text=f'Привет {message.from_user.username}'
    # регистрация?
    await message.answer(text)

@router.message(Command("me"))
async def cmd_start(message: Message):
    await message.answer(f"chat_id:     {message.chat.id}\n" + 
                         f"first_name:  {message.from_user.first_name}\n" +
                         f"last_name:   {message.from_user.last_name}\n" +
                         f"username:    {message.from_user.username}")

@router.message(Command("clear"))
async def cmd_start(message: Message):
    pass
