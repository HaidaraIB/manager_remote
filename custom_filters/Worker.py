from telegram import Update
from telegram.ext.filters import UpdateFilter
import models


class Worker(UpdateFilter):
    def filter(self, update: Update):
        try:
            d_agent = models.DepositAgent.get_workers(
                worker_id=update.effective_user.id
            )
            p_agent = models.PaymentAgent.get_workers(
                worker_id=update.effective_user.id
            )
            checker = models.Checker.get_workers(worker_id=update.effective_user.id)
            if p_agent or d_agent or checker:
                return True
            return False
        except:
            return False
