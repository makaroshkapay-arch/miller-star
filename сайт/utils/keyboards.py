from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 Баланс", callback_data="balance"),
        InlineKeyboardButton(text="🎁 Маркет", callback_data="market")
    )
    builder.row(
        InlineKeyboardButton(text="🛒 Купить звезды", callback_data="buy_stars"),
        InlineKeyboardButton(text="💎 Продать звезды", callback_data="sell_stars")
    )
    builder.row(
        InlineKeyboardButton(text="📦 Продать подарок", callback_data="sell_gift"),
        InlineKeyboardButton(text="🔗 Кошелек", callback_data="wallet")
    )
    builder.row(
        InlineKeyboardButton(text="📋 История", callback_data="history"),
        InlineKeyboardButton(text="❓ Поддержка", callback_data="support")
    )
    return builder.as_markup()

def back_button(callback: str = "back_to_menu") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=callback))
    return builder.as_markup()

def payment_methods() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⭐ Telegram Stars", callback_data="pay_stars"),
        InlineKeyboardButton(text="💎 TON (Send Wallet)", callback_data="pay_ton")
    )
    builder.row(
        InlineKeyboardButton(text="💰 USDT (TRC20)", callback_data="pay_usdt"),
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")
    )
    return builder.as_markup()

def gift_card(gift_id: int, price: float, seller_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=f"⭐ Купить за {price} звезд", callback_data=f"buy_gift_{gift_id}")
    )
    builder.row(
        InlineKeyboardButton(text="❓ Договориться", callback_data=f"contact_seller_{seller_id}"),
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_market")
    )
    return builder.as_markup()