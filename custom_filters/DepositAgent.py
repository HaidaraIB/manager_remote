from telegram import Update
from telegram.ext.filters import UpdateFilter
import models


class DepositAgent(UpdateFilter):
    def filter(self, update: Update):
        try:
            d_agent = models.DepositAgent.get_workers(
                worker_id=update.effective_user.id
            )
            if d_agent:
                return True
            return False
        except:
            return False
