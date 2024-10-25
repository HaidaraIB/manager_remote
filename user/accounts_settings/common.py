from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from common.common import build_accounts_keyboard, build_back_button, format_amount
from common.functions import send_deposit_without_check
from common.constants import *
from common.back_to_home_page import back_to_user_home_page_button
import user.accounts_settings.accounts_settings as accounts_settings
import models
import os
import random


def build_accounts_settings_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                text="إنشاء حساب موثق ™️",
                callback_data="create account",
            ),
            InlineKeyboardButton(
                text="حذف حساب 🗑",
                callback_data="delete account",
            ),
        ],
        back_to_user_home_page_button[0],
    ]
    return InlineKeyboardMarkup(keyboard)


async def reply_with_user_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    accounts = build_accounts_keyboard(user_id=update.effective_user.id)
    if not accounts:
        await accounts_settings.accounts_settings(update, context)
        return
    keybaord = [
        accounts,
        build_back_button("back_to_accounts_settings"),
        back_to_user_home_page_button[0],
    ]
    await update.callback_query.edit_message_text(
        text="اختر حساباً من حساباتك المسجلة لدينا",
        reply_markup=InlineKeyboardMarkup(keybaord),
    )


def check_balance_condition(context: ContextTypes.DEFAULT_TYPE):
    if context.bot_data.get("create_account_deposit_pin", None) is None:
        context.bot_data["create_account_deposit"] = 0
        context.bot_data["create_account_deposit_pin"] = 0

    return context.bot_data["create_account_deposit"] > 0


def choose_random_amount(context: ContextTypes.DEFAULT_TYPE):
    rand = random.randint(1000, 10000)
    if rand >= context.bot_data["create_account_deposit"]:
        rand = context.bot_data["create_account_deposit"]
        context.bot_data["create_account_deposit"] = 0
    else:
        context.bot_data["create_account_deposit"] -= rand

    return rand


async def serve_gift(
    user_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    account: models.Account,
):
    deposit_gift = choose_random_amount(context=context)
    await send_deposit_without_check(
        context=context,
        acc_number=account.acc_num,
        user_id=user_id,
        amount=deposit_gift,
        method=CREATE_ACCOUNT_DEPOSIT,
    )
    gift_line = f"قيمة الهدية: <b>{format_amount(deposit_gift)} ل.س</b>\n\n"
    group_text = (
        "تم إنشاء حساب جديد مشحون بمبلغ ✅\n\n"
        f"رقم الحساب: <code>{account.acc_num}</code>\n"
    ) + gift_line
    await context.bot.send_message(
        chat_id=int(os.getenv("CHANNEL_ID")),
        text=group_text,
        message_thread_id=int(
            os.getenv("DEPOSIT_GIFT_ON_CREATE_ACCOUNT_SUCCESS_TOPIC_ID")
        ),
    )
    return gift_line, deposit_gift
