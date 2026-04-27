import secrets
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from database import get_db, GiftListing, UserDB, Transaction, EscrowTrade
from sqlalchemy import select
from datetime import datetime, timedelta
from config import config
from utils.keyboards import back_button

router = Router()

class SellGiftState(StatesGroup):
    waiting_for_name = State()
    waiting_for_year = State()
    waiting_for_rarity = State()
    waiting_for_price = State()
    waiting_for_verification = State()

@router.message(Command("sell"))
async def cmd_sell_gift(message: Message, state: FSMContext):
    text = (
        "📦 <b>Продажа подарка</b>\n\n"
        "Давайте добавим ваш подарок в маркетплейс!\n\n"
        "🔹 <b>Шаг 1 из 5:</b> Введите название подарка\n\n"
        "<i>Пример: Коллекционная роза Telegram 2024</i>"
    )
    await message.answer(text, parse_mode="HTML")
    await state.set_state(SellGiftState.waiting_for_name)

@router.message(SellGiftState.waiting_for_name)
async def process_gift_name(message: Message, state: FSMContext):
    await state.update_data(gift_name=message.text)
    text = "🔹 <b>Шаг 2 из 5:</b> Введите год выпуска подарка\n\n<i>Пример: 2023</i>"
    await message.answer(text, parse_mode="HTML")
    await state.set_state(SellGiftState.waiting_for_year)

@router.message(SellGiftState.waiting_for_year)
async def process_gift_year(message: Message, state: FSMContext):
    try:
        year = int(message.text)
        if year < 2015 or year > 2025:
            raise ValueError
        await state.update_data(gift_year=year)
        
        text = (
            "🔹 <b>Шаг 3 из 5:</b> Выберите редкость подарка\n\n"
            "Отправьте цифру:\n"
            "1 - Обычный ⚪\n"
            "2 - Редкий 🔵\n"
            "3 - Эпический 🟣\n"
            "4 - Легендарный 🟡"
        )
        await message.answer(text, parse_mode="HTML")
        await state.set_state(SellGiftState.waiting_for_rarity)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный год (2015-2025)")

@router.message(SellGiftState.waiting_for_rarity)
async def process_gift_rarity(message: Message, state: FSMContext):
    rarity_map = {"1": "common", "2": "rare", "3": "epic", "4": "legendary"}
    rarity = rarity_map.get(message.text)
    
    if not rarity:
        await message.answer("❌ Пожалуйста, выберите 1, 2, 3 или 4")
        return
    
    await state.update_data(gift_rarity=rarity)
    
    text = (
        "🔹 <b>Шаг 4 из 5:</b> Укажите цену в звездах\n\n"
        f"<i>Минимальная цена: {config.MIN_TRADE_AMOUNT} звезд</i>"
    )
    await message.answer(text, parse_mode="HTML")
    await state.set_state(SellGiftState.waiting_for_price)

@router.message(SellGiftState.waiting_for_price)
async def process_gift_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        if price < config.MIN_TRADE_AMOUNT:
            await message.answer(f"❌ Минимальная цена: {config.MIN_TRADE_AMOUNT} звезд")
            return
        
        await state.update_data(price_stars=price)
        
        # Генерируем код верификации
        verify_code = secrets.token_hex(8)
        await state.update_data(verify_code=verify_code)
        
        text = (
            "🔹 <b>Шаг 5 из 5:</b> Верификация подарка\n\n"
            f"⚠️ <b>Важно!</b> Чтобы подтвердить владение подарком, "
            f"отправьте код <code>{verify_code}</code> в любой чат "
            f"вместе с подарком (как комментарий) и сделайте скриншот.\n\n"
            f"После этого отправьте скриншот боту."
        )
        await message.answer(text, parse_mode="HTML")
        await state.set_state(SellGiftState.waiting_for_verification)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную цену")

@router.message(SellGiftState.waiting_for_verification, F.photo)
async def process_gift_verification(message: Message, state: FSMContext):
    data = await state.get_data()
    
    # Сохраняем объявление в БД
    async with await get_db() as session:
        listing = GiftListing(
            seller_id=message.from_user.id,
            gift_name=data["gift_name"],
            gift_year=data["gift_year"],
            gift_rarity=data["gift_rarity"],
            price_stars=data["price_stars"],
            verification_code=data["verify_code"]
        )
        session.add(listing)
        await session.commit()
        
        # Списание комиссии за размещение
        user = await UserDB.get(session, message.from_user.id)
        if user:
            fee = data["price_stars"] * config.PLATFORM_FEE / 100
            user.stars_balance -= min(fee, 5)  # Мин комиссия 5 звезд
        
        await session.commit()
    
    text = (
        f"✅ <b>Подарок успешно добавлен в маркетплейс!</b>\n\n"
        f"🎁 <b>Название:</b> {data['gift_name']}\n"
        f"📅 <b>Год:</b> {data['gift_year']}\n"
        f"⭐ <b>Цена:</b> {data['price_stars']} звезд\n\n"
        f"Покупатели смогут найти ваш подарок через /market"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=back_button())
    await state.clear()

@router.message(Command("buy"))
async def cmd_buy_gift(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Используйте: /buy ID_подарка\n\nПосмотреть ID можно в /market")
        return
    
    try:
        gift_id = int(args[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом")
        return
    
    async with await get_db() as session:
        result = await session.execute(
            select(GiftListing).where(GiftListing.id == gift_id, GiftListing.is_active == True)
        )
        gift = result.scalar_one_or_none()
        
        if not gift:
            await message.answer("❌ Подарок не найден или уже продан")
            return
        
        user = await UserDB.get(session, message.from_user.id)
        
        if not user or user.stars_balance < gift.price_stars:
            await message.answer(
                f"❌ Недостаточно звезд. Нужно: {gift.price_stars} ⭐\n"
                f"Пополните баланс через /buy_stars"
            )
            return
        
        # Для крупных сделок используем эскроу
        if gift.price_stars >= 500:
            # Создаем эскроу-сделку
            trade_id = secrets.token_hex(4).upper()
            escrow = EscrowTrade(
                trade_id=trade_id,
                seller_id=gift.seller_id,
                buyer_id=message.from_user.id,
                gift_id=gift.id,
                amount=gift.price_stars,
                expires_at=datetime.utcnow() + timedelta(minutes=30)
            )
            session.add(escrow)
            
            text = (
                f"🔒 <b>Крупная сделка! Используется эскроу-счёт</b>\n\n"
                f"🎁 <b>Подарок:</b> {gift.gift_name}\n"
                f"⭐ <b>Сумма:</b> {gift.price_stars} звезд\n"
                f"🆔 <b>ID сделки:</b> <code>{trade_id}</code>\n\n"
                f"Средства заморожены до завершения сделки.\n"
                f"После получения подарка, подтвердите транзакцию командой /confirm_trade {trade_id}"
            )
            await message.answer(text, parse_mode="HTML")
        else:
            # Обычная сделка
            user.stars_balance -= gift.price_stars
            
            # Начисляем продавцу (минус комиссия)
            seller = await UserDB.get(session, gift.seller_id)
            if seller:
                commission = gift.price_stars * config.PLATFORM_FEE / 100
                seller.stars_balance += gift.price_stars - commission
                seller.total_trades += 1
            
            gift.is_active = False
            user.total_trades += 1
            
            await session.commit()
            
            # Уведомляем продавца
            await message.bot.send_message(
                gift.seller_id,
                f"✅ <b>Ваш подарок продан!</b>\n\n"
                f"🎁 {gift.gift_name}\n"
                f"⭐ Сумма: {gift.price_stars} звезд\n"
                f"Покупатель: {message.from_user.first_name}",
                parse_mode="HTML"
            )
            
            await message.answer(
                f"✅ <b>Поздравляем с покупкой!</b>\n\n"
                f"🎁 {gift.gift_name} добавлен в вашу коллекцию.\n\n"
                f"Продавец свяжется с вами для передачи подарка.",
                parse_mode="HTML"
            )
        
        await session.commit()