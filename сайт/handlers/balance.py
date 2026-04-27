from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database import get_db, UserDB
from sqlalchemy import select
from config import config
from utils.keyboards import back_button
import logging

logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("balance"))
async def cmd_balance(message: Message):
    """
    Обработчик команды /balance — показывает текущий баланс пользователя
    """
    try:
        async with await get_db() as session:
            # Получаем пользователя из БД
            user = await UserDB.get(session, message.from_user.id)

            if not user:
                # Если пользователя нет в БД — создаём его
                user = UserDB(
                    user_id=message.from_user.id,
            )
            session.add(user)
            await session.commit()

            # Обновляем объект после коммита, чтобы получить ID
            user = await UserDB.get(session, message.from_user.id)

        # Формируем сообщение с балансом
        balance_text = (
            f"💰 <b>Ваш баланс</b>\n\n"
            f"⭐ <b>Звёзд:</b> {user.stars_balance}\n"
            f"💎 <b>Алмазов:</b> {user.diamonds_balance}\n\n"
            f"📊 <b>Всего сделок:</b> {user.total_trades}\n"
            f"🏆 <b>Рейтинг:</b> #{user.rating_position}"
        )

        await message.answer(
            balance_text,
            parse_mode="HTML",
            reply_markup=back_button()
        )

    except Exception as e:
        logger.error(f"Ошибка при получении баланса: {e}")
        await message.answer("❌ Произошла ошибка при получении баланса. Попробуйте позже.")

@router.message(F.text.contains("баланс") | F.text.contains("Balance"))
async def balance_fallback(message: Message):
    """
    Дополнительный обработчик — реагирует на сообщения с словом «баланс»
    """
    await cmd_balance(message)