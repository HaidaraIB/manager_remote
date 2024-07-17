from telegram import (
    Update,
)

import re

from telegram.ext.filters import UpdateFilter

class TeamCash(UpdateFilter):
    def filter(self, update: Update):
        try:
            team_cash_info = update.message.text.split("\n")
            return (
                bool(re.search(r"^User ID : .+$", team_cash_info[0]))
                and bool(re.search(r"^Password : .+$", team_cash_info[1]))
                and bool(re.search(r"^Workplace ID : \d+$", team_cash_info[2]))
            )
        except:
            return False
