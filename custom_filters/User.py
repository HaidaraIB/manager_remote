from telegram import Update
from telegram.ext.filters import UpdateFilter
import models


class User(UpdateFilter):
    def filter(self, update: Update):
        try:
            admins = models.Admin.get_admin_ids()
            admin_ids = [admin.id for admin in admins]

            return update.effective_user.id not in admin_ids
        except:
            return False
