import secrets
from datetime import datetime  # добавлен импорт datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command  # добавлен импорт Command
from database import get_db, UserDB, Transaction
from config import config
from utils.keyboards import back_button, payment_methods
import qrcode
from io import BytesIO
import logging  # добавлен импорт logging для логирования ошибок

logger = logging.getLogger(__name__)

router = Router()

# Цены на звезды
STARS_PACKAGES = {
    100: {"stars": 100, "price_usdt": 1.20},
    500: {"stars": 500, "price_usdt": 6.00},
    1000: {"stars": 1000, "price_usdt": 12.00},
    5000: {"stars": 5000, "price_usdt": 60.00},
}

@router.message(Command("buy_stars"))
@router.callback_query(F.data == "buy_stars")
async def buy_stars_menu(event):
    if isinstance(event, CallbackQuery):
        message = event.message
        await event.answer()
    else:
        message = event

    text = "💰 <b>Пополнение звезд</b> 💰\n\nВыберите сумму пополнения:\n\n"

    buttons = []
    for stars, info in STARS_PACKAGES.items():
        buttons.append([InlineKeyboardButton(
            text=f"⭐ {stars} звезд - {info['price_usdt']:.2f} USDT",
            callback_data=f"buy_package_{stars}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")])

    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"  # исправлено: убрана лишняя кавычка
    )

@router.callback_query(F.data.startswith("buy_package_"))
async def process_purchase(callback: CallbackQuery):
    try:
        stars_amount = int(callback.data.split("_")[2])
        package = STARS_PACKAGES[stars_amount]

        # Генерируем уникальный ID транзакции
        tx_id = secrets.token_hex(16)

        # Сохраняем транзакцию в БД
        async with await get_db() as session:
            tx = Transaction(
                user_id=callback.from_user.id,
                type="buy_stars",
                amount_stars=stars_amount,
                amount_crypto=package["price_usdt"],
                status="pending",
                tx_hash=tx_id
            )
            session.add(tx)
            await session.commit()

        text = (
            f"💎 <b>Оплата {stars_amount} звезд</b>\n\n"
            f"💰 <b>Сумма:</b> {package['price_usdt']} USDT\n\n"
            f"📤 <b>Реквизиты для оплаты:</b>\n"
            f"<code>{config.CRYPTO_WALLET}</code>\n\n"
            f"🔗 <b>Сеть:</b> TRC20 (USDT)\n\n"
            f"⚡ <b>ID транзакции:</b> <code>{tx_id}</code>\n\n"
            f"<i>После оплаты, отправьте чек боту командой /confirm {tx_id}</i>"
        )

        # Генерируем QR-код
        qr = qrcode.QRCode(box_size=4, border=2)
        qr.add_data(config.CRYPTO_WALLET)
        qr.make()
        img = qr.make_image(fill_color="black", back_color="white")

        bio = BytesIO()
        img.save(bio, "PNG")
        bio.seek(0)

        await callback.message.delete()
        await callback.message.answer_photo(
            photo=bio,
            caption=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"confirm_payment_{tx_id}")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_menu")]
            ])
        )
        await callback.answer()
        bio.close()  # закрыт буфер BytesIO
    except Exception as e:
        logger.error(f"Ошибка при обработке покупки звёзд: {e}")
        await callback.message.answer("❌ Произошла ошибка при обработке запроса. Попробуйте позже.")
        await callback.answer()

@router.message(Command("confirm"))
async def confirm_payment(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Используйте: /confirm TX_ID")
        return

    tx_id = args[1]

    try:
        async with await get_db() as session:
            from sqlalchemy import select
            result = await session.execute(select(Transaction).where(Transaction.tx_hash == tx_id))
            tx = result.scalar_one_or_none()

            if tx and tx.status == "pending":
                tx.status = "completed"
                tx.completed_at = datetime.utcnow()

                # Начисляем звезды пользователю
                user = await UserDB.get(session, message.from_user.id)
                if user:
                    user.stars_balance += tx.amount_stars
                    user.total_trades += 1

                await session.commit()
                await message.answer(f"✅ Оплата подтверждена! Вам начислено {tx.amount_stars} ⭐")
            else:
                await message.answer("❌ Транзакция не найдена или уже обработана")
    except Exception as e:
        logger.error(f"Ошибка при подтверждении платежа: {e}")
        await message.answer("❌ Произошла ошибка при подтверждении платежа. Попробуйте позже.")
