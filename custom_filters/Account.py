from telegram import (
    Update,
)

from telegram.ext.filters import UpdateFilter


class Account(UpdateFilter):
    def filter(self, update: Update):
        return (
            update.effective_message.reply_to_message.caption
            and update.effective_message.reply_to_message.caption.split("\n")[
                0
            ].isnumeric()
        )
