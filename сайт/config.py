import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
    
    # Send Wallet
    SEND_WALLET_TOKEN = os.getenv("SEND_WALLET_TOKEN")
    CRYPTO_WALLET = os.getenv("CRYPTO_WALLET")
    
    # Настройки платформы
    PLATFORM_FEE = float(os.getenv("PLATFORM_FEE", 1.0))
    MIN_TRADE_AMOUNT = float(os.getenv("MIN_TRADE_AMOUNT", 10))
    
    # База данных
    DATABASE_URL = "sqlite+aiosqlite:///miller_stars.db"
    
    # Валюты
    STARS_TO_USDT_RATE = 0.012  # 1 Star = 0.012 USDT (примерный курс)

config = Config()