from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
import re

import telebot
from telebot import types





class Tbot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token, parse_mode=None)
        self.user_lang = {}
        self.current_group = {}
        self.user_data = {}


    def run(self):
        @self.bot.message_handler(commands=['help', 'start'])
        def send_welcome(message):
            self.bot.reply_to(message, """\
            Hi there! You can control me with these commands:

            /cg <group> - Change the currently selected group
            /group - Show the currently selected group
            /lang - Change the lang (used for displaying schedule days)
            /today - Display schedule for today 
            /tomorrow - Display schedule for tomorrow
            /week - Display schedule for this week
            """)
            lang(message)


        @self.bot.message_handler(commands=['lang'])
        def lang(message):
            markup = types.InlineKeyboardMarkup(row_width=2)

            button_lang1 = types.InlineKeyboardButton("eng 🇺🇸", callback_data="change_lang_to_eng")
            button_lang2 = types.InlineKeyboardButton("fin 🇫🇮", callback_data="change_lang_to_fin")

            markup.add(button_lang1, button_lang2)
            self.bot.send_message(message.chat.id, "Choose a language:", reply_markup=markup)


        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_handler(call):
            chat_id = call.message.chat.id
            
            if call.data == "change_lang_to_eng":
                self.user_lang[chat_id] = 'eng'
                self.bot.answer_callback_query(call.id, "You changed your language to english")
            elif call.data == "change_lang_to_fin":
                self.user_lang[chat_id] = 'fin'
                self.bot.answer_callback_query(call.id, "You changed your language to finnish")




        @self.bot.message_handler(commands=['cg'])
        def change_group(message):
            chat_id = message.chat.id
            new_group = message.text.split("/cg ", 1)[-1]

            self.current_group[chat_id] = new_group.upper()
            self.bot.send_message(chat_id, f"Group has been changed to: {self.current_group[chat_id]}")
            raw_data_days, data_events = self.fetch_data_for_group(self.current_group[chat_id])
            self.user_data[chat_id] = {'raw_data_days': raw_data_days, 'data_events': data_events}


        @self.bot.message_handler(commands=['group'])
        def display_current_group(message):
            chat_id = message.chat.id

            if chat_id in self.current_group:
                self.bot.send_message(chat_id, f"Current Group: {self.current_group[chat_id]}")
            else:
                self.bot.send_message(chat_id, "Current group is not set. Use /cg to set it.")




        @self.bot.message_handler(commands=['tomorrow'])
        def display_tomorrow_schedule(message):
            chat_id = message.chat.id

            if chat_id in self.current_group:
                if chat_id in self.user_lang:
                    try:
                        raw_data_days = self.user_data[chat_id]['raw_data_days']
                        data_events = self.user_data[chat_id]['data_events']
                        day_index = 1

                        if self.user_lang[chat_id] == 'fin':
                            message_send = raw_data_days[day_index] + '\n' + data_events[day_index]
                        else:
                            message_send = self.replace_day_abbreviations(raw_data_days[day_index]) + '\n' + data_events[day_index]

                        self.bot.reply_to(message, f"{message_send}")
                    except (IndexError, KeyError):
                        self.bot.send_message(chat_id, "Error! There's no data for tomorrow or the group is not set.")
                else:
                    self.bot.send_message(chat_id, "Please set your language preference using /lang.")
            else:
                self.bot.send_message(chat_id, "Current group is not set. Use /cg to set it.")



        @self.bot.message_handler(commands=['today'])
        def display_today_schedule(message):
            chat_id = message.chat.id

            if chat_id in self.current_group:
                if chat_id in self.user_lang:
                    try:
                        raw_data_days = self.user_data[chat_id]['raw_data_days']
                        data_events = self.user_data[chat_id]['data_events']
                        day_index = 0

                        if self.user_lang[chat_id] == 'fin':
                            message_send = raw_data_days[day_index] + '\n' + data_events[day_index]
                        else:
                            message_send = self.replace_day_abbreviations(raw_data_days[day_index]) + '\n' + data_events[day_index]

                        self.bot.reply_to(message, f"{message_send}")
                    except (IndexError, KeyError):
                        self.bot.send_message(chat_id, "Error! There's no data for today or the group is not set.")
                else:
                    self.bot.send_message(chat_id, "Please set your language preference using /lang.")
            else:
                self.bot.send_message(chat_id, "Current group is not set. Use /cg to set it.")



        @self.bot.message_handler(commands=['week'])
        def display_today_week(message):
            chat_id = message.chat.id

            if chat_id in self.current_group:
                if chat_id in self.user_lang:
                    try:
                        raw_data_days = self.user_data[chat_id]['raw_data_days']
                        data_events = self.user_data[chat_id]['data_events']

                        for x in range(len(data_events)):
                            if self.user_lang[chat_id] == 'fin':
                                message_send = raw_data_days[x] + '\n' + data_events[x]
                            else:
                                message_send = self.replace_day_abbreviations(raw_data_days[x]) + '\n' + data_events[x]

                            self.bot.reply_to(message, f"{message_send}")
                    except (IndexError, KeyError):
                        self.bot.send_message(chat_id, "Error! There's no data for this week.")
                else:
                    self.bot.send_message(chat_id, "Please set your language preference using /lang.")
            else:
                self.bot.send_message(chat_id, "Current group is not set. Use /cg to set it.")

        self.bot.infinity_polling()




    def fetch_data_for_group(self, group):
        options = Options()
        options.add_argument('-headless')
        driver = webdriver.Firefox(options=options)

        driver.get("https://lukkarit.oamk.fi/")
        javascript_code = f"updateBasket('addGroup', '{group}');"
        driver.execute_script(javascript_code)
        driver.execute_script("viewCal();")

        try:
            WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'td.nd')))
            raw_data = driver.find_elements(By.CSS_SELECTOR, "td.nd")  # nd and nd today
            raw_data_today = driver.find_element(By.CSS_SELECTOR, "td.nd.today")  # nd and nd today
        except:
            print("An error occurred, sorry")

        L = []
        for i in raw_data:
            L.append(i.text)

        raw_data_days = L[L.index(raw_data_today.text):5]
        raw_data_events = L[L.index(raw_data_today.text) + 5:]
        data_events = []

        for i in raw_data_events:
            data_events_el = re.sub(r'\n+', '\n', i)
            data_events.append(data_events_el)

        driver.quit()

        return raw_data_days, data_events


    def replace_day_abbreviations(self, item):
        words = item.split()
        day_abbrev = words[0]
        fin_to_eng = {'Ma': 'Mo', 'Ti': 'Tu', 'Ke': 'Wen', 'To': 'Th', 'Pe': 'Fr' }
        replacement = fin_to_eng.get(day_abbrev, day_abbrev)
        return replacement + ' ' + words[1]


if __name__ == "__main__":
    from botr import *



