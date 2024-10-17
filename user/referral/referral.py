from telegram import Chat, Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.helpers import create_deep_linked_url
import models


async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        referrals = models.Referral.get_by(referrer_id=update.effective_user.id)
        text = (
            f"عدد المسجلين عن طريق رابط الدعوة الخاص بك: <b>{len(referrals)}</b>\n\n"
            "رابط الدعوة الخاص بك:\n"
            f"{create_deep_linked_url(context.bot.username, payload=str(update.effective_user.id))}\n\n"
            "اضغط /start للعودة إلى القائمة الرئيسية."
        )
        await update.callback_query.edit_message_text(text=text)


referral_handler = CallbackQueryHandler(referral, "referral")
