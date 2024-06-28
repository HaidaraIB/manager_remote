from telegram import (
    Update,
)

from telegram.ext.filters import UpdateFilter
from DB import DB


class Worker(UpdateFilter):
    def filter(self, update: Update):
        d_agent = DB.get_deposit_agent(user_id=update.effective_user.id)
        p_agent = DB.get_payment_agent(user_id=update.effective_user.id)
        checker = DB.get_checker(user_id=update.effective_user.id)
        if p_agent or d_agent or checker:
            return True
        return False
