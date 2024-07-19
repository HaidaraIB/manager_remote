from telegram import Update
from telegram.ext.filters import UpdateFilter
import database


class Worker(UpdateFilter):
    def filter(self, update: Update):
        try:
            d_agent = database.DepositAgent.get_workers(
                worker_id=update.effective_user.id
            )
            p_agent = database.PaymentAgent.get_workers(
                worker_id=update.effective_user.id
            )
            checker = database.Checker.get_workers(worker_id=update.effective_user.id)
            if p_agent or d_agent or checker:
                return True
            return False
        except:
            return False
