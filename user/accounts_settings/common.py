from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from common.common import build_accounts_keyboard, notify_workers, build_back_button
from common.back_to_home_page import back_to_user_home_page_button
from common.stringifies import stringify_deposit_order
from common.constants import CREATE_ACCOUNT_DEPOSIT
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


def find_valid_amounts(context: ContextTypes.DEFAULT_TYPE, amounts: list):
    valid_amounts = []
    for a in amounts:
        reminder = context.bot_data["create_account_deposit"] - a
        if reminder > 0:
            valid_amounts.append(a)

    return valid_amounts


def choose_random_amount(context: ContextTypes.DEFAULT_TYPE, valid_amounts: float):
    rand = random.choice(valid_amounts)
    context.bot_data["create_account_deposit"] -= rand

    return rand


async def send_deposit_on_create_account_seccess(
    context: ContextTypes.DEFAULT_TYPE,
    acc_number: int,
    user_id: int,
    valid_amounts: list,
):
    target_group = context.bot_data["data"]["deposit_orders_group"]
    amount = choose_random_amount(context=context, valid_amounts=valid_amounts)
    serial = await models.DepositOrder.add_deposit_order(
        user_id=user_id,
        group_id=target_group,
        method=CREATE_ACCOUNT_DEPOSIT,
        amount=amount,
        acc_number=acc_number,
    )
    order_text = stringify_deposit_order(
        amount=amount,
        serial=serial,
        method=CREATE_ACCOUNT_DEPOSIT,
        account_number=acc_number,
    )

    message = await context.bot.send_message(
        chat_id=context.bot_data["data"]["deposit_after_check_group"],
        text=order_text,
        reply_markup=InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(
                text="قبول الطلب ✅",
                callback_data=f"verify_deposit_order_{serial}",
            )
        ),
    )

    await models.DepositOrder.send_order(
        pending_process_message_id=message.id,
        serial=serial,
        group_id=context.bot_data["data"]["deposit_after_check_group"],
        ex_rate=0,
    )
    workers = models.DepositAgent.get_workers(is_point=False)
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه تم استلام إيداع إنشاء حساب جديد 🚨",
        )
    )
    return amount
