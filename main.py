from dotenv import load_dotenv
from firebase import init_firebase;
from keep_alive import keep_alive;
import bot;

if __name__ == "__main__":
  load_dotenv();
  keep_alive();
  init_firebase();
  bot.init_bot();
