from telegram import (
    Update,
)

from telegram.ext.filters import UpdateFilter


class Withdraw(UpdateFilter):
    def filter(self, update: Update):
        try:
            return (
                update.message.reply_to_message.text.startswith("تفاصيل طلب سحب")
                and update.message.reply_to_message.reply_markup.inline_keyboard[0][0]
                .callback_data.split("_")[-1]
                .isnumeric()
            )
        except:
            return False
