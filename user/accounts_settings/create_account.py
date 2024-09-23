from telegram import Update, Chat, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from common.decorators import (
    check_if_user_present_decorator,
    check_user_call_on_or_off_decorator,
)
from common.common import build_user_keyboard, format_amount, build_back_button
from common.force_join import check_if_user_member_decorator
from common.back_to_home_page import back_to_user_home_page_button
from common.constants import HOME_PAGE_TEXT
from user.accounts_settings.common import (
    send_deposit_on_create_account_seccess,
    find_valid_amounts,
)
import models
import asyncio
import os
from datetime import datetime

create_account_lock = asyncio.Lock()


@check_user_call_on_or_off_decorator
@check_if_user_present_decorator
@check_if_user_member_decorator
async def create_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_accounts_settings"),
            back_to_user_home_page_button[0],
        ]
        if context.user_data.get("pending_create_account", False):
            await update.callback_query.answer(
                text="لديك طلب قيد التنفيذ بالفعل",
                show_alert=True,
            )
            return

        accounts = models.Account.get_user_accounts(user_id=update.effective_user.id)
        if len(accounts) >= 2:
            await update.callback_query.edit_message_text(
                text=(
                    "بعد التحديث الجديد أصبح يسمح لكل لاعب بحسابين عن طريق البوت فقط.\n"
                    "لن نقوم بحذف حساباتك القديمة ولكن لن تتمكن من إنشاء حساب جديد إلا عندما يكون لديك أقل من حسابين في البوت.\n"
                    "بالإضافة إلى أنه أصبح بإمكانك حذف حساب عن طريق زر حذف حساب الجديد.\n"
                    "ملاحظة: تستطيع إنشاء حساب جديد مرة كل 15 يوماً، ولن تستطيع حذفه إلا بعد مرور هذه المدة أيضاً."
                ),
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return
        elif accounts and (datetime.now() - accounts[0].connect_to_user_date).days < 15:
            await update.callback_query.edit_message_text(
                text="تستطيع إنشاء حساب جديد مرة كل 15 يوماً",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return

        await update.callback_query.edit_message_text(
            text="لحظات، طلبك قيد المعالجة..."
        )
        await create_account_lock.acquire()
        account = models.Account.get_account(new=True)
        if account:
            context.user_data["pending_create_account"] = True
            await asyncio.sleep(5)

            if context.bot_data.get("create_account_deposit_pin", None) is None:
                context.bot_data["create_account_deposit"] = 0
                context.bot_data["create_account_deposit_pin"] = 0

            valid_amounts = find_valid_amounts(
                context=context,
                amounts=[5000, 10000, 15000, 20000, 25000, 50000],
                large_amount=50000,
            )

            if not valid_amounts and context.bot_data["create_account_deposit"] > 0:
                valid_amounts.append(context.bot_data["create_account_deposit"])
                context.bot_data["create_account_deposit"] = 0

            gift_line = ""
            deposit_gift = 0
            if valid_amounts:
                deposit_gift = await send_deposit_on_create_account_seccess(
                    context=context,
                    acc_number=account.acc_num,
                    user_id=update.effective_user.id,
                    valid_amounts=valid_amounts,
                )
                gift_line = f"قيمة الهدية: <b>{format_amount(deposit_gift)} ل.س</b>\n\n"
                group_text = (
                    "تم إنشاء حساب جديد مشحون بمبلغ ✅\n\n"
                    f"رقم الحساب: <code>{account.acc_num}</code>\n"
                ) + gift_line

                await context.bot.send_message(
                    chat_id=int(os.getenv("CHANNEL_ID")),
                    text=group_text,
                    message_thread_id=1503,
                )

            await models.Account.connect_account_to_user(
                user_id=update.effective_user.id,
                acc_num=account.acc_num,
                deposit_gift=deposit_gift,
            )

            text = (
                (
                    "تمت الموافقة على طلبك لإنشاء حساب ✅\n\n"
                    "معلومات الحساب:\n\n"
                    f"رقم الحساب: <code>{account.acc_num}</code>\n"
                    f"كلمة المرور: <code>{account.password}</code>\n\n"
                )
                + gift_line
                + f"اضغط /start للمتابعة"
            )

            await update.callback_query.edit_message_text(text=text)
            context.user_data["pending_create_account"] = False
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
