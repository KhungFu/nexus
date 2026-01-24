# -*- coding: utf-8 -*-
import telebot, os
from logger import nexus_logger
class TelegramBot:
    def __init__(self):
        token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_USER_ID")
        self.bot = telebot.TeleBot(token) if token else None
    def send_report(self, message):
        try:
            if self.bot: self.bot.send_message(self.chat_id, message, parse_mode="Markdown")
        except Exception as e:
            nexus_logger.log_error("TELEGRAM_MSG", e)
