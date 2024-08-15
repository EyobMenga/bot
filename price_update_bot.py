import asyncio
import aiohttp
from telegram import Bot
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
TELEGRAM_BOT_TOKEN = "7027869606:AAFsEFHhDXiXJONRnMA4wi6U911lebARhd0"
TELEGRAM_CHANNEL_ID = "-1002029137458"
LIVECOINWATCH_API_URL = "https://api.livecoinwatch.com/coins/map"
LIVECOINWATCH_API_KEY = "585ece63-7d83-4c90-9842-3f8264616096"
COINS = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "XRP": "Ripple",
    "LTC": "Litecoin"
}

# Initialize Telegram bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def fetch_data(url, headers=None, json=None):
    try:
        logger.info(f"Fetching data from {url} with headers {headers} and json {json}")
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=json) as response:
                if response.status == 200:
                    logger.info(f"Successfully fetched data from {url}")
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch data from {url}: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Exception occurred during fetch_data: {e}")
        return None

async def fetch_coin_prices():
    logger.info("Fetching coin prices")
    headers = {
        "x-api-key": LIVECOINWATCH_API_KEY,
        "Content-Type": "application/json"
    }
    json_data = {
        "codes": list(COINS.keys()),
        "currency": "USD",
        "sort": "rank",
        "order": "ascending",
        "offset": 0,
        "limit": 10,  # Adjust limit as needed
        "meta": False
    }
    data = await fetch_data(LIVECOINWATCH_API_URL, headers=headers, json=json_data)
    
    if data:
        logger.info(f"Raw data received: {data}")
    
    price_updates = []
    if data:
        for coin in data:
            logger.info(f"Processing coin data: {coin}")
            code = coin.get("code", "UNKNOWN").upper()
            name = COINS.get(code, "Unknown Coin")
            rate = coin.get("rate", 0)
            price_updates.append(f"🔹 {name} ({code}): ${rate:.2f}")
    
    if price_updates:
        logger.info(f"Fetched coin prices: {price_updates}")
        return "\n".join(price_updates)
    return None

async def post_to_telegram(content):
    try:
        await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=content, parse_mode='Markdown')
        logger.info(f"Posted to Telegram: {content[:50]}...")
    except Exception as e:
        logger.error(f"Error posting to Telegram: {e}")

async def main():
    try:
        prices = await fetch_coin_prices()
        if prices:
            message = f"💡 *Price Updates:*\n\n{prices}\n\nStay updated with the latest in crypto! 🚀\n\n@Ai_cryptos_news"
            await post_to_telegram(message)
    except Exception as e:
        logger.error(f"Error in main function: {e}")

if __name__ == "__main__":
    asyncio.run(main())
