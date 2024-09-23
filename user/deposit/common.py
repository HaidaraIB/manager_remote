from telegram import Update, Chat, InlineKeyboardMarkup
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
)
from common.decorators import (
    check_user_pending_orders_decorator,
    check_user_call_on_or_off_decorator,
    check_if_user_present_decorator,
    check_if_user_created_account_from_bot_decorator,
)
from user.accounts_settings.common import reply_with_user_accounts
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
        await reply_with_user_accounts(update, context)
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

            if amount <= 0:
                await update.message.reply_text(
                    text="الرجاء إرسال قيمة موجبة تماماً",
                    reply_markup=InlineKeyboardMarkup(back_to_deposit_method_buttons),
                )
                return

            elif method == BEMO and amount < 50000:
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
        context.user_data["wal_num_deposit"] = wal.number
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
        deposit_wallet = context.user_data["wal_num_player_deposit"]
        method = SYRCASH
        target_group = context.bot_data["data"]["deposit_orders_group"]
        amount = context.user_data["player_deposit_amount"]
        agent_id = update.effective_user.id
        gov = context.user_data[f"{context.user_data['agent_option']}_point"]
    else:
        user_id = update.effective_user.id
        ref_num = update.message.text
        acc_number = context.user_data["account_deposit"]
        deposit_wallet = context.user_data["wal_num_deposit"]
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
    serial = await models.DepositOrder.add_deposit_order(
        user_id=user_id,
        group_id=target_group,
        method=method,
        acc_number=acc_number,
        deposit_wallet=deposit_wallet,
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
            wal=deposit_wallet,
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
