from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database import get_db, GiftListing
from sqlalchemy import select
from utils.keyboards import gift_card, back_button

router = Router()

@router.message(Command("market"))
@router.callback_query(F.data == "market")
async def show_market(event: Message | CallbackQuery):
    # Определяем тип события и получаем сообщение
    if isinstance(event, CallbackQuery):
        message = event.message
        await event.answer()  # обязательный ответ на callback
    else:
        message = event

    try:
        async with await get_db() as session:
            result = await session.execute(
                select(GiftListing).where(GiftListing.is_active == True).limit(20)
            )
            gifts = result.scalars().all()

        if not gifts:
            text = "🎁 <b>Маркетплейс подарков</b>\n\nВ данный момент нет активных объявлений.\n\nХотите продать свой подарок? Используйте команду /sell"
            await message.answer(text, parse_mode="HTML", reply_markup=back_button())
            return

        text = "🎁 <b>Доступные подарки</b> 🎁\n\n"

        for gift in gifts[:5]:  # Показываем по 5 подарков
            rarity_emoji = {
                "common": "⚪", "rare": "🔵", "epic": "🟣", "legendary": "🟡"
            }.get(gift.gift_rarity, "⚪")

            text += (
                f"{rarity_emoji} <b>{gift.gift_name}</b>\n"
                f"📅 Год: {gift.gift_year}\n"
                f"⭐ Цена: {gift.price_stars} звезд\n"
                f"🆔 ID: {gift.id}\n"
                f"━━━━━━━━━━━━━━━\n"
            )

        text += "\n<i>Нажмите на ID подарка для покупки /buy ID</i>"
        await message.answer(text, parse_mode="HTML", reply_markup=back_button("back_to_menu"))

    except Exception as e:
        logger.error(f"Ошибка при загрузке маркетплейса: {e}")
        error_text = "❌ Произошла ошибка при загрузке маркетплейса. Попробуйте позже."
        await message.answer(error_text, reply_markup=back_button())
