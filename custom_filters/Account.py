from telegram import Update
from telegram.ext.filters import UpdateFilter
import re


class Account(UpdateFilter):
    def filter(self, update: Update):
        try:
            return update.message.reply_to_message.reply_markup.inline_keyboard[0][
                0
            ].callback_data.startswith("decline_create_account") and bool(
                re.search(
                    r"^[\u0600-\u06FF ]+\n\d+\n[a-zA-Z0-9]+$",
                    update.message.text,
                )
            )

        except:
            return False
