from telegram import Update
from telegram.ext.filters import UpdateFilter
import models


class Agent(UpdateFilter):
    def filter(self, update: Update):
        try:
            agent = models.TrustedAgent.get_workers(user_id=update.effective_user.id)
            return True if agent else False
        except:
            return False
