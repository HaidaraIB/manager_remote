from telegram import Update
from telegram.ext.filters import UpdateFilter
import re


class Account(UpdateFilter):
    def filter(self, update: Update):
        try:
            return update.message.reply_to_message.text.split("\n")[
                3
            ].isnumeric() and bool(
                re.search(
                    r"^\D+\n\d+\n[a-zA-Z0-9]+$",
                    update.message.text,
                )
            )

        except:
            return False
