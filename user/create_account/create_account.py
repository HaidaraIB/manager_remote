from telegram import Update, Chat, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from common.decorators import (
    check_if_user_present_decorator,
    check_user_call_on_or_off_decorator,
)
from common.common import build_user_keyboard
from common.force_join import check_if_user_member_decorator
from common.back_to_home_page import back_to_user_home_page_button
from common.constants import HOME_PAGE_TEXT
import models
import asyncio

create_account_lock = asyncio.Lock()


@check_user_call_on_or_off_decorator
@check_if_user_present_decorator
@check_if_user_member_decorator
async def create_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if context.user_data.get("pending_create_account", False):
            await update.callback_query.answer(
                text="لديك طلب قيد التنفيذ بالفعل",
                show_alert=True,
            )
            return

        accounts = models.Account.get_user_accounts(user_id=update.effective_user.id)
        if len(accounts) > 2:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=(
                    "بعد التحديث الجديد أصبح يسمح لكل لاعب بحسابين عن طريق البوت فقط\n"
                    "لن نقوم بحذف حساباتك القديمة ولكن لن تتمكن من إنشاء حساب جديد إلا عندما يكون لديك أقل من حسابين في البوت\n"
                    "بالإضافة إلى أنه أصبح بإمكانك حذف حساب عن طريق زر حذف حساب الجديد"
                ),
                reply_markup=InlineKeyboardMarkup(back_to_user_home_page_button),
            )
            return
        await update.callback_query.edit_message_text(
            text="لحظات، طلبك قيد المعالجة..."
        )
        await create_account_lock.acquire()
        account = models.Account.get_account(new=True)
        if account:
            await models.Account.connect_account_to_user(
                user_id=update.effective_user.id, acc_num=account.acc_num
            )
            context.user_data["pending_create_account"] = True
            await asyncio.sleep(5)
            text = (
                "تمت الموافقة على طلبك لإنشاء حساب ✅\n\n"
                "معلومات الحساب:\n\n"
                f"رقم الحساب: <code>{account.acc_num}</code>\n"
                f"كلمة المرور: <code>{account.password}</code>\n\n"
                f"اضغط /start للمتابعة"
            )
            await update.callback_query.edit_message_text(text=text)
        else:
            await update.callback_query.answer(
                text="المعذرة، ليس لدينا حسابات حالياً",
                show_alert=True,
            )
            await update.callback_query.edit_message_text(
                text=HOME_PAGE_TEXT,
                reply_markup=build_user_keyboard(),
            )
        create_account_lock.release()


create_account_handler = CallbackQueryHandler(create_account, "^create account$")
