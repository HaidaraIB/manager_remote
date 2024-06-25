from telegram import (
    Update,
)

from telegram.ext.filters import (
    UpdateFilter
)

class ResponseToUserComplaint(UpdateFilter):
    def filter(self, update: Update):
        try:
            if self.name == "close complaint":
                return update.message.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data['name'] == "skip close complaint"
            else:
                return update.message.reply_to_message.reply_markup.inline_keyboard[0][0].callback_data['name'] == "back from respond to user complaint"
        except:
            return False