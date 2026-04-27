from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from database import get_db, UserDB
from utils.keyboards import main_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    async with await get_db() as session:
        user = await UserDB.create_or_update(
            session, 
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name
        )
    
    welcome_text = (
        f"✨ <b>Добро пожаловать в Miller Stars Bot!</b> ✨\n\n"
        f"⭐ <b>Ваш баланс:</b> {user.stars_balance:.2f} звезд\n\n"
        f"<b>🚀 Что я умею:</b>\n"
        f"• Покупать и продавать звезды Telegram\n"
        f"• Торговать коллекционными подарками\n"
        f"• Принимать оплату криптовалютой\n\n"
        f"<i>Выберите действие в меню ниже:</i>"
    )
    
    await message.answer(welcome_text, reply_markup=main_menu(), parse_mode="HTML")

@router.message(Command("balance"))
async def cmd_balance(message: Message):
    async with await get_db() as session:
        user = await UserDB.get(session, message.from_user.id)
        if user:
            balance_text = (
                f"💰 <b>Ваш баланс</b> 💰\n\n"
                f"⭐ <b>Звезды:</b> {user.stars_balance:.2f}\n"
                f"💎 <b>В криптокошельке:</b> (подключите кошелек)\n\n"
                f"<i>Пополнить баланс можно через /buy_stars</i>"
            )
            await message.answer(balance_text, parse_mode="HTML")

@router.callback_query(F.data == "balance")
async def callback_balance(callback: CallbackQuery):
    async with await get_db() as session:
        user = await UserDB.get(session, callback.from_user.id)
        balance_text = (
            f"💰 <b>Ваш баланс</b> 💰\n\n"
            f"⭐ <b>Звезды:</b> {user.stars_balance:.2f}\n\n"
            f"📈 <b>Статистика:</b>\n"
            f"• Всего сделок: {user.total_trades}\n\n"
            f"/buy_stars - пополнить баланс\n"
            f"/sell_stars - продать звезды"
        )
        await callback.message.edit_text(balance_text, parse_mode="HTML", reply_markup=back_button())
    await callback.answer()

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=main_menu()
    )
    await callback.answer()