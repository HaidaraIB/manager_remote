from telegram import Update
from telegram.ext.filters import UpdateFilter
import models


class Admin(UpdateFilter):
    def filter(self, update: Update):
        try:
            admins = models.Admin.get_admin_ids()
            admin_ids = [admin.id for admin in admins]

            return update.effective_user.id in admin_ids
        except:
            return False
