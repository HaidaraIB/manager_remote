from telegram import (
    Update,
)

from telegram.ext.filters import UpdateFilter


class Deposit(UpdateFilter):
    def filter(self, update: Update):
        return (
            update.message.reply_to_message.caption
            and update.message.reply_to_message.caption.startswith("إيداع جديد:")
        )
