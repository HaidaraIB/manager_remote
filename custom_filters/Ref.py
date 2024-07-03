from telegram import (
    Update,
)

import re

from telegram.ext.filters import UpdateFilter

from common.common import payment_method_pattern


class Ref(UpdateFilter):
    def filter(self, update: Update):
        try:
            ref_info = update.message.text.split("\n")
            return (
                bool(re.search(r"^رقم العملية: \d+$", ref_info[0]))
                and payment_method_pattern(ref_info[1])
                and bool(re.search(r"^المبلغ: \d+.?\d*$", ref_info[2]))
            )
        except:
            return False
