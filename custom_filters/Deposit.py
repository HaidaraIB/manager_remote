from telegram import (
    Update,
)

from telegram.ext.filters import UpdateFilter


class Deposit(UpdateFilter):
    def filter(self, update: Update):
        try:
            return (
                update.message.reply_to_message.text
                and update.message.reply_to_message.text.startswith("إيداع جديد:")
            )
        except:
            return False
