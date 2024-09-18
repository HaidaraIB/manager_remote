from telegram import Update, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from worker.check_deposit.check_deposit import check_deposit
from common.back_to_home_page import back_to_user_home_page_button
from common.stringifies import stringify_deposit_order
from common.force_join import check_if_user_member_decorator
from common.constants import *
from common.common import (
    notify_workers,
    build_methods_keyboard,
    build_back_button,
    send_to_photos_archive,
)
from common.decorators import (
    check_user_pending_orders_decorator,
    check_user_call_on_or_off_decorator,
    check_if_user_present_decorator,
    check_if_user_created_account_from_bot_decorator,
)

import models
import asyncio
import os

(
    ACCOUNT_DEPOSIT,
    DEPOSIT_METHOD,
    DEPOSIT_AMOUNT,
    REF_NUM,
) = range(4)


@check_user_pending_orders_decorator
@check_user_call_on_or_off_decorator
@check_if_user_present_decorator
@check_if_user_member_decorator
@check_if_user_created_account_from_bot_decorator
async def make_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        accounts = models.Account.get_user_accounts(user_id=update.effective_user.id)
        accounts_keyboard = [
            InlineKeyboardButton(
                text=a.acc_num,
                callback_data=str(a.acc_num),
            )
            for a in accounts
        ]
        keybaord = [
            accounts_keyboard,
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="اختر حساباً من حساباتك المسجلة لدينا",
            reply_markup=InlineKeyboardMarkup(keybaord),
        )
        return ACCOUNT_DEPOSIT


async def account_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not update.callback_query.data.startswith("back"):
            context.user_data["account_deposit"] = int(update.callback_query.data)
        deposit_methods = build_methods_keyboard()
        deposit_methods.append(build_back_button("back_to_account_number_deposit"))
        deposit_methods.append(back_to_user_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر وسيلة الدفع 💳",
            reply_markup=InlineKeyboardMarkup(deposit_methods),
        )
        return DEPOSIT_METHOD


back_to_account_deposit = make_deposit


async def choose_deposit_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_choose_deposit_method"),
            back_to_user_home_page_button[0],
        ]

        if not update.callback_query.data.startswith("back"):
            method_name = update.callback_query.data
            context.user_data["deposit_method"] = method_name
        else:
            method_name = context.user_data["deposit_method"]

        text = (
            ("أدخل المبلغ أكبر من 50 ألف\n" "الحد الأدنى للإيداع = 50,000 ل.س")
            if method_name == BEMO
            else "أرسل مبلغ الإيداع"
        )

        if not update.callback_query.data.startswith("back"):
            method = models.PaymentMethod.get_payment_method(name=method_name)
            if not method.on_off:
                await update.callback_query.answer(
                    "هذه الوسيلة متوقفة مؤقتاً ❗️",
                    show_alert=True,
                )
                return

            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.delete_message()
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )

        return DEPOSIT_AMOUNT


back_to_choose_deposit_method = account_deposit


async def get_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_to_get_deposit_amount_buttons = [
            build_back_button("back_to_get_deposit_amount"),
            back_to_user_home_page_button[0],
        ]
        back_to_deposit_method_buttons = [
            build_back_button("back_to_choose_deposit_method"),
            back_to_user_home_page_button[0],
        ]

        method = context.user_data["deposit_method"]

        if update.message:
            amount = float(update.message.text)

            if method == BEMO and amount < 50000:
                await update.message.reply_text(
                    text="الحد الأدنى للإيداع = 50,000 ل.س",
                    reply_markup=InlineKeyboardMarkup(back_to_deposit_method_buttons),
                )
                return

            context.user_data["deposit_amount"] = amount
        else:
            amount = context.user_data["deposit_amount"]

        wal = models.Wallet.get_wallets(amount=amount, method=method)
        if not wal:
            await update.message.reply_text(
                text=(
                    "المبلغ المدخل تجاوز الحد المسموح لحسابات الشركة ❗️\n"
                    "جرب مع قيمة أصغر"
                ),
                reply_markup=InlineKeyboardMarkup(back_to_deposit_method_buttons),
            )
            return

        text = (
            f"قم بإرسال المبلغ المراد إيداعه إلى:\n\n"
            f"<code>{wal.number}</code>\n\n"
            f"ثم أرسل رقم عملية الدفع إلى البوت لنقوم بتوثيقها.\n\n"
        ) + (
            "<b>ملاحظة هامة: الشبكة المستخدمه هي TRC20</b>\n" if method == USDT else ""
        )

        if update.message:
            if method == BEMO:
                await update.message.reply_photo(
                    photo=os.getenv("BEMO_REF_NUMBER_GUIDE_PHOTO_ID"),
                    caption=text,
                    reply_markup=InlineKeyboardMarkup(
                        back_to_get_deposit_amount_buttons
                    ),
                )
            else:
                await update.message.reply_text(
                    text=text,
                    reply_markup=InlineKeyboardMarkup(
                        back_to_get_deposit_amount_buttons
                    ),
                )

        else:
            if method == BEMO:
                await update.callback_query.edit_message_caption(
                    caption=text,
                    reply_markup=InlineKeyboardMarkup(
                        back_to_get_deposit_amount_buttons
                    ),
                )
            else:
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=InlineKeyboardMarkup(
                        back_to_get_deposit_amount_buttons
                    ),
                )
        return REF_NUM


back_to_get_deposit_amount = choose_deposit_method


async def send_to_check_deposit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    is_player_deposit: bool = False,
):
    if is_player_deposit:
        user_id = update.effective_user.id
        ref_num = update.message.text
        acc_number = context.user_data["player_number"]
        method = SYRCASH
        target_group = context.bot_data["data"]["deposit_orders_group"]
        amount = context.user_data["player_deposit_amount"]
        agent_id = update.effective_user.id
        gov = context.user_data[f"{context.user_data['agent_option']}_point"]
    else:
        user_id = update.effective_user.id
        ref_num = update.message.text
        acc_number = context.user_data["account_deposit"]
        method = context.user_data["deposit_method"]
        target_group = context.bot_data["data"]["deposit_orders_group"]
        amount = context.user_data["deposit_amount"]
        agent_id = 0
        gov = ""

    ref_present = models.RefNumber.get_ref_number(
        number=ref_num,
        method=method,
    )
    order_present = models.DepositOrder.get_one_order(ref_num=ref_num, method=method)
    if (ref_present and ref_present.order_serial != -1) or (
        order_present and order_present.state == "approved"
    ):
        return False
    deposit_wallet = models.Wallet.get_wallets(amount=amount, method=method)
    serial = await models.DepositOrder.add_deposit_order(
        user_id=user_id,
        group_id=target_group,
        method=method,
        acc_number=acc_number,
        deposit_wallet=deposit_wallet.number,
        amount=amount,
        ref_number=ref_num,
        agent_id=agent_id,
        gov=gov,
    )

    context.job_queue.run_once(
        callback=check_deposit,
        user_id=user_id,
        when=60,
        data=serial,
        name="1_deposit_check",
        job_kwargs={
            "misfire_grace_time": None,
            "coalesce": True,
        },
    )

    message = await context.bot.send_message(
        chat_id=target_group,
        text=stringify_deposit_order(
            amount=amount,
            serial=serial,
            method=method,
            account_number=acc_number,
            wal=deposit_wallet.number,
            ref_num=ref_num,
        ),
    )

    await models.DepositOrder.add_message_ids(
        serial=serial,
        pending_check_message_id=message.id,
    )

    workers = models.DepositAgent.get_workers(is_point=False)
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه يوجد طلب إيداع قيد التحقق رقم العملية <code>{ref_num}</code> 🚨",
        )
    )
    return True


async def send_to_check_point_deposit(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id

    photo = update.message.photo[-1]
    ref_number = context.user_data["point_deposit_ref_num"]
    deposit_wallet = models.Wallet.get_wallets(
        amount=context.user_data["player_deposit_amount"],
    )
    amount = context.user_data["point_deposit_amount"]
    gov = context.user_data["point_deposit_point"]
    agent = models.TrustedAgent.get_workers(user_id=user_id, gov=gov)

    target_group = context.bot_data["data"]["deposit_orders_group"]

    serial = await models.DepositOrder.add_deposit_order(
        user_id=user_id,
        group_id=target_group,
        method=SYRCASH,
        deposit_wallet=deposit_wallet,
        amount=amount,
        ref_number=ref_number,
        agent_id=user_id,
        gov=agent.gov,
    )

    text = stringify_deposit_order(
        amount=amount,
        serial=serial,
        method=SYRCASH,
        wal=deposit_wallet,
        ref_num=ref_number,
        workplace_id=agent.team_cash_workplace_id,
    )
    markup = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(
            text="التحقق ☑️", callback_data=f"check_deposit_order_{serial}"
        )
    )
    message = await context.bot.send_photo(
        chat_id=target_group,
        photo=photo,
        caption=text,
        reply_markup=markup,
    )
    await send_to_photos_archive(
        context=context,
        photo=photo,
        serial=serial,
        order_type="deposit",
    )

    await models.DepositOrder.add_message_ids(
        serial=serial,
        pending_check_message_id=message.id,
    )

    workers = models.DepositAgent.get_workers(is_point=True)
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه إيداع جديد قيد التحقق 🚨",
        )
    )
    workers = models.Checker.get_workers(check_what="deposit", method=POINT_DEPOSIT)
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه يوجد طلب تحقق إيداع جديد 🚨",
        )
    )
