import subprocess
import time

def run_script(script):
    try:
        subprocess.run(["python", script], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {script}: {e}")

def run_news_bot():
    run_script("news_bot.py")

def run_price_update_bot():
    run_script("price_update_bot.py")

def main():
    last_price_update_time = time.time() - 20  # Initialize to run immediately

    # Run both bots initially
    run_news_bot()
    run_price_update_bot()

    while True:
        current_time = time.time()

        # Run news bot every 10 minutes
        if (current_time - last_price_update_time) >= 600:
            run_news_bot()
            last_price_update_time = current_time

        # Run price update bot every 3 hours
        if (current_time - last_price_update_time) >= 10800:
            run_price_update_bot()
            last_price_update_time = current_time

        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()

