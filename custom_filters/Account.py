from telegram import (
    Update,
)

from telegram.ext.filters import UpdateFilter


class Account(UpdateFilter):
    def filter(self, update: Update):
        try:
            return (
                update.message.reply_to_message.text
                and update.message.reply_to_message.text.split("\n")[3].isnumeric()
            )
        except:
            return False
