from telegram import Update
from telegram.ext.filters import UpdateFilter
import re


class Account(UpdateFilter):
    def filter(self, update: Update):
        try:
            return bool(
                re.search(
                    pattern=r"^\d+\n[a-zA-Z0-9]+$",
                    string=update.message.text,
                )
            )

        except:
            return False
