from telegram import (
    Update,
)

from telegram.ext.filters import UpdateFilter


class Complaint(UpdateFilter):
    def filter(self, update: Update):
        return (
            update.message
            and update.message.reply_to_message
            and update.message.reply_to_message.text
            and (
                update.message.reply_to_message.text.startswith("شكوى جديدة")
                or update.message.reply_to_message.text.startswith("ملحق بالشكوى")
            )
        )
