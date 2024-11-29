from telegram import Update
from telegram.ext.filters import UpdateFilter
from common.common import payment_method_pattern
from common.constants import BANKS
import re


class Ref(UpdateFilter):
    def filter(self, update: Update):
        try:
            ref_info = update.message.text.split("\n")
            if ref_info[1] in BANKS:
                return (
                    bool(re.search(r"^رقم العملية: [0-9]+$", ref_info[0]))
                    and payment_method_pattern(ref_info[1])
                    and bool(re.search(r"^المبلغ: \d+\.?\d*$", ref_info[2]))
                    and bool(re.search(r"^الكنية: [\u0621-\u064A]+$", ref_info[3]))
                )
            return (
                bool(re.search(r"^رقم العملية: [0-9]+$", ref_info[0]))
                and payment_method_pattern(ref_info[1])
                and bool(re.search(r"^المبلغ: \d+\.?\d*$", ref_info[2]))
            )
        except:
            return False
