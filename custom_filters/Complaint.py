from telegram import (
    Update,
)

from telegram.ext.filters import UpdateFilter


class Complaint(UpdateFilter):
    def filter(self, update: Update):
        try:
            return update.message.reply_to_message.text.startswith(
                "شكوى جديدة"
            ) or update.message.reply_to_message.text.startswith("ملحق بالشكوى")
        except:
            return False
