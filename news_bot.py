import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from telegram import Bot
from telegram.constants import ParseMode
import logging
import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager  # Added webdriver-manager
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
TELEGRAM_BOT_TOKEN = "7027869606:AAFsEFHhDXiXJONRnMA4wi6U911lebARhd0"
TELEGRAM_CHANNEL_ID = "-1002029137458"
COINDESK_URL = "https://www.coindesk.com/livewire"
COINTELEGRAPH_URL = "https://cointelegraph.com/category/latest-news"
DB_FILE = "posted_urls.db"

# Initialize Telegram bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS posted_urls (
                        url TEXT PRIMARY KEY,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )''')
    conn.commit()
    conn.close()

def save_posted_url(url):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO posted_urls (url) VALUES (?)", (url,))
    conn.commit()
    conn.close()

def has_url_been_posted(url):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM posted_urls WHERE url = ?", (url,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def setup_webdriver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def fetch_data_with_selenium(url, wait_time=10):
    driver = setup_webdriver()
    try:
        driver.get(url)
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        page_source = driver.page_source
        return page_source
    except Exception as e:
        logger.error(f"Error fetching data from {url} with Selenium: {e}")
        return None
    finally:
        driver.quit()

async def parse_coindesk_news(html):
    soup = BeautifulSoup(html, 'html.parser')
    news_posts = []
    for div in soup.find_all('div', class_='side-cover-cardstyles__SideCoverCardData-sc-1nd3s5z-2'):
        date_str = div.find('span', class_='typography__StyledTypography-sc-owin6q-0 iOUkmj').text
        post_date = datetime.strptime(date_str, "%B %d, %Y").replace(tzinfo=timezone.utc)
        title = div.find('h4', class_='typography__StyledTypography-sc-owin6q-0 dtjHgI').text
        url = div.find('a', class_='card-title-link')['href']
        description = div.find('p', class_='typography__StyledTypography-sc-owin6q-0 kDZZDY').text
        full_url = f"https://www.coindesk.com{url}"

        news_posts.append({
            "date": post_date,
            "title": title,
            "url": full_url,
            "description": description
        })
    return news_posts

async def parse_cointelegraph_news(html):
    soup = BeautifulSoup(html, 'html.parser')
    news_posts = []
    for article in soup.find_all('article', class_='post-card-inline'):
        title_tag = article.find('a', class_='post-card-inline__title-link')
        title = title_tag.text.strip()
        url = f"https://cointelegraph.com{title_tag['href']}"
        description = article.find('p', class_='post-card-inline__text').text.strip()
        date_str = article.find('time', class_='post-card-inline__date')['datetime']
        post_date = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
        
        news_posts.append({
            "date": post_date,
            "title": title,
            "url": url,
            "description": description
        })
    return news_posts

async def fetch_and_post_coindesk_news():
    html = fetch_data_with_selenium(COINDESK_URL)
    if html:
        news_posts = await parse_coindesk_news(html)
        for post in news_posts:
            if not has_url_been_posted(post['url']):
                message = f"*{post['title']}*\n\n{post['description']}\n\n[Read More]({post['url']})\n\n@Aicryptosnews"
                await post_to_telegram(message)
                save_posted_url(post['url'])
                await asyncio.sleep(1)  # Avoid rate limits

async def fetch_and_post_cointelegraph_news():
    html = fetch_data_with_selenium(COINTELEGRAPH_URL)
    if html:
        news_posts = await parse_cointelegraph_news(html)
        for post in news_posts:
            if not has_url_been_posted(post['url']):
                message = f"*{post['title']}*\n\n{post['description']}\n\n[Read More]({post['url']})\n\n@Aicryptosnews"
                await post_to_telegram(message)
                save_posted_url(post['url'])
                await asyncio.sleep(1)  # Avoid rate limits

async def post_to_telegram(content, parse_mode=ParseMode.MARKDOWN):
    try:
        if len(content) > 4096:
            for i in range(0, len(content), 4096):
                await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=content[i:i+4096], parse_mode=parse_mode)
        else:
            await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=content, parse_mode=parse_mode)
        logger.info(f"Posted to Telegram: {content[:50]}...")
    except Exception as e:
        logger.error(f"Error posting to Telegram: {e}")

async def main():
    init_db()
    end_time = datetime.now() + timedelta(hours=5, minutes=55)
    try:
        while datetime.now() < end_time:
            await fetch_and_post_coindesk_news()
            await fetch_and_post_cointelegraph_news()
            await asyncio.sleep(600)  # Check every 10 minutes
    except Exception as e:
        logger.error(f"Error in main function: {e}")
    finally:
        logger.info("Bot has stopped running after 5 hours and 58 minutes.")

if __name__ == "__main__":
    asyncio.run(main())









