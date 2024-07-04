from telegram import (
    Update,
)

from telegram.ext.filters import UpdateFilter
from DB import DB


class DepositAgent(UpdateFilter):
    def filter(self, update: Update):
        try:
            d_agent = DB.get_deposit_agent(user_id=update.effective_user.id)
            if d_agent:
                return True
            return False
        except:
            return False
