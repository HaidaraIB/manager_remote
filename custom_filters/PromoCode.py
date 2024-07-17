from telegram import (
    Update,
)

import re

from telegram.ext.filters import UpdateFilter

class PromoCode(UpdateFilter):
    def filter(self, update: Update):
        try:
            promo_code_info = update.message.text.split("\n")
            return (
                bool(re.search(r"^Username : .+$", promo_code_info[0]))
                and bool(re.search(r"^Password : .+$", promo_code_info[1]))
            )
        except:
            return False
