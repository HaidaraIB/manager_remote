from telegram import (
    Update,
)

from telegram.ext.filters import UpdateFilter


class Ref(UpdateFilter):
    def filter(self, update: Update):
        try:
            return update.message.reply_to_message.reply_markup.inline_keyboard[0][
                0
            ].callback_data.startswith("cancel_add_ref")
        except:
            return False
