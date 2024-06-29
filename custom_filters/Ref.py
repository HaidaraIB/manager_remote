from telegram import (
    Update,
)

from telegram.ext.filters import UpdateFilter

from common.common import payment_method_pattern


class Ref(UpdateFilter):
    def filter(self, update: Update):
        try:
            ref_info = update.message.text.split("\n")
            return (
                ref_info[0].isnumeric()
                and payment_method_pattern(ref_info[1])
                and ref_info[2].isnumeric()
            )
        except:
            return False
