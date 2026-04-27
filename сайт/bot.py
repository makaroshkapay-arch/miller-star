#!/usr/bin/env python3
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from database import init_db
from handlers import start, balance, market, payments, gifts, admin

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

session = AiohttpSession(proxy="SOCKS5://134.122.64.174:1080")
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Подключаем роутеры
dp.include_router(start.router)
dp.include_router(balance.router)
dp.include_router(market.router)
dp.include_router(payments.router)
dp.include_router(gifts.router)
dp.include_router(admin.router)

async def set_commands():
    """Устанавливаем команды бота в меню"""
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="balance", description="💰 Мой баланс"),
        BotCommand(command="market", description="🎁 Маркетплейс"),
        BotCommand(command="buy", description="🛒 Купить подарок"),
        BotCommand(command="sell", description="📦 Продать подарок"),
        BotCommand(command="buy_stars", description="⭐ Купить звезды"),
        BotCommand(command="sell_stars", description="💎 Продать звезды"),
        BotCommand(command="wallet", description="🔗 Мой кошелек"),
        BotCommand(command="support", description="❓ Поддержка"),
    ]
    await bot.set_my_commands(commands)

async def main():
    try:
        # Инициализация базы данных
        await init_db()
        logger.info("База данных инициализирована")

        # Установка команд бота
        await set_commands()
        logger.info("Команды бота установлены")

        # Запуск бота
        logger.info("Бот запущен")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}")
        raise

    finally:
        # Graceful shutdown
        await bot.session.close()
        logger.info("Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
