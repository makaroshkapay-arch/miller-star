from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from config import config
from database import get_db, UserDB

router = Router()

# Фильтр для админов
def admin_filter(message: Message):
    return message.from_user.id in config.ADMIN_IDS

@router.message(Command("admin"), admin_filter)
async def admin_panel(message: Message):
    text = (
        "👑 <b>Админ-панель Miller Stars Bot</b>\n\n"
        "📊 <b>Доступные команды:</b>\n"
        "/stats - Статистика бота\n"
        "/give_stars ID СУММА - Выдать звезды\n"
        "/ban ID - Забанить пользователя\n"
        "/broadcast ТЕКСТ - Рассылка\n\n"
        "<i>Скоро будут добавлены новые функции</i>"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(Command("stats"), admin_filter)
async def bot_stats(message: Message):
    async with await get_db() as session:
        from sqlalchemy import func, select
        from database import User, Transaction
        
        total_users = await session.scalar(select(func.count()).select_from(User))
        total_trades = await session.scalar(select(func.sum(User.total_trades)).select_from(User))
        
        text = (
            f"📊 <b>Статистика бота</b>\n\n"
            f"👥 <b>Пользователей:</b> {total_users}\n"
            f"💰 <b>Всего сделок:</b> {total_trades or 0}\n"
            f"⭐ <b>Баланс бота:</b> (не реализовано)\n\n"
            f"<i>Бот работает стабильно</i>"
        )
        await message.answer(text, parse_mode="HTML")