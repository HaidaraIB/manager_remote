from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from common.common import build_accounts_keyboard, notify_workers, build_back_button
from common.back_to_home_page import back_to_user_home_page_button
import user.accounts_settings.accounts_settings as accounts_settings
import models
import asyncio
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


def check_balance_condition(context:ContextTypes.DEFAULT_TYPE):
    if context.bot_data.get("create_account_deposit_pin", None) is None:
        context.bot_data["create_account_deposit"] = 0
        context.bot_data["create_account_deposit_pin"] = 0

    return context.bot_data["create_account_deposit"] > 0

def choose_random_amount(context: ContextTypes.DEFAULT_TYPE):
    rand = random.randint(1000, 30000)
    if rand >= context.bot_data["create_account_deposit"]:
        rand = context.bot_data["create_account_deposit"]
        context.bot_data["create_account_deposit"] = 0
    else:
        context.bot_data["create_account_deposit"] -= rand

    return rand
