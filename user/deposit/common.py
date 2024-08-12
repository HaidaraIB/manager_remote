from telegram import (
    PhotoSize,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    Chat,
)
from telegram.ext import ContextTypes, ConversationHandler
from models import DepositOrder, DepositAgent, Account
from common.common import (
    notify_workers,
    send_to_media_archive,
    build_user_keyboard,
    build_methods_keyboard,
    build_back_button,
)
from common.decorators import (
    check_if_user_created_account_from_bot_decorator,
    check_if_user_present_decorator,
    check_user_call_on_or_off_decorator,
    check_user_pending_orders_decorator,
)
from common.stringifies import stringify_deposit_order
from common.constants import *
from common.back_to_home_page import back_to_user_home_page_button
from common.force_join import check_if_user_member_decorator
from models import PaymentMethod
import asyncio

SEND_MONEY_TEXT = (
    "قم بإرسال المبلغ المراد إيداعه إلى:\n\n"
    "<code>{}</code>\n"
    "<code>{}</code>"
    "ثم أرسل لقطة شاشة أو ملف pdf لعملية الدفع إلى البوت لنقوم بتوثيقها.\n\n"
    "Send the money to:\n\n"
    "<code>{}</code>\n"
    "<code>{}</code>"
    "And send a screenshot or a pdf in order to confirm it."
)

ACCOUNT_DEPOSIT, DEPOSIT_METHOD, SCREENSHOT, DEPOSIT_AMOUNT = range(4)


@check_user_pending_orders_decorator
@check_user_call_on_or_off_decorator
@check_if_user_present_decorator
@check_if_user_member_decorator
@check_if_user_created_account_from_bot_decorator
async def make_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if update.callback_query.data == "deposit_without_acc":
            context.user_data["acc_from_bot"] = False
            keybaord = [
                back_to_user_home_page_button[0],
            ]
        else:
            context.user_data["acc_from_bot"] = True
            accounts = Account.get_user_accounts(user_id=update.effective_user.id)
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
            text="اختر حساباً من حساباتك المسجلة لدينا - Choose an account",
            reply_markup=InlineKeyboardMarkup(keybaord),
        )
        return ACCOUNT_DEPOSIT


async def account_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_account_deposit"),
            back_to_user_home_page_button[0],
        ]
        if update.message:
            context.user_data["account_deposit"] = int(update.message.text)
        elif not update.callback_query.data.startswith("back"):
            context.user_data["account_deposit"] = int(update.callback_query.data)
        if update.message:
            await update.message.reply_text(
                text="أدخل المبلغ - Enter the amount",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text="أدخل المبلغ - Enter the amount",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return DEPOSIT_AMOUNT


back_to_account_deposit = make_deposit


async def deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        deposit_methods = build_methods_keyboard()
        deposit_methods.append(build_back_button("back_to_deposit_amount"))
        deposit_methods.append(back_to_user_home_page_button[0])
        if update.message:
            context.user_data["deposit_amount"] = float(update.message.text)
            await update.message.reply_text(
                text="اختر وسيلة الدفع 💳 - Choose payment method 💳",
                reply_markup=InlineKeyboardMarkup(deposit_methods),
            )
        else:
            await update.callback_query.edit_message_text(
                text="اختر وسيلة الدفع 💳 - Choose payment method 💳",
                reply_markup=InlineKeyboardMarkup(deposit_methods),
            )
        return DEPOSIT_METHOD


back_to_deposit_amount = account_deposit


async def deposit_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        data = update.callback_query.data
        method = PaymentMethod.get_payment_method(name=data)
        if method.on_off == 0:
            await update.callback_query.answer(METHOD_IS_OFF_TEXT)
            return
        context.user_data["deposit_method"] = data
        back_buttons = [
            build_back_button("back_to_deposit_method"),
            back_to_user_home_page_button[0],
        ]
        if data not in AEBAN_LIST:
            text = SEND_MONEY_TEXT.format(
                context.bot_data["data"][f"{data}_number"],
                "\n",
                context.bot_data["data"][f"{data}_number"],
                "\n",
            )
            if data == USDT:
                text += "<b>ملاحظة هامة: الشبكة المستخدمه هي TRC20 - Note that the network is TRC20</b>\n"
        else:
            text = SEND_MONEY_TEXT.format(
                context.bot_data["data"][f"{data}_number"],
                str(context.bot_data["data"][f"{data}_aeban"]) + "\n\n",
                context.bot_data["data"][f"{data}_number"],
                str(context.bot_data["data"][f"{data}_aeban"]) + "\n\n",
            )
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return SCREENSHOT


back_to_deposit_method = deposit_amount


async def send_to_check_deposit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id
    proof = (
        update.message.photo[-1] if update.message.photo else update.message.document
    )

    amount = context.user_data["deposit_amount"]
    acc_number = context.user_data["account_deposit"]
    acc_from_bot = context.user_data["acc_from_bot"]
    method = context.user_data["deposit_method"]
    target_group = context.bot_data["data"]["deposit_orders_group"]

    serial = await DepositOrder.add_deposit_order(
        user_id=user_id,
        method=method,
        acc_number=acc_number,
        acc_from_bot=acc_from_bot,
        group_id=target_group,
        amount=amount,
        deposit_wallet=context.bot_data["data"][f"{method}_number"],
    )

    caption = stringify_deposit_order(
        amount=amount,
        account_number=acc_number,
        method=method,
        serial=serial,
        wal=context.bot_data["data"][f"{method}_number"],
        acc_from_bot=acc_from_bot,
    )
    markup = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(
            text="التحقق ☑️", callback_data=f"check_deposit_order_{serial}"
        )
    )
    if isinstance(proof, PhotoSize):
        message = await context.bot.send_photo(
            chat_id=target_group,
            photo=proof,
            caption=caption,
            reply_markup=markup,
        )
    else:
        message = await context.bot.send_document(
            chat_id=target_group,
            document=proof,
            caption=caption,
            reply_markup=markup,
        )

    await send_to_media_archive(
        context,
        media=proof,
        serial=serial,
        order_type="deposit",
    )

    await DepositOrder.add_message_ids(
        serial=serial, pending_check_message_id=message.id
    )

    workers = DepositAgent.get_workers()
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه يوجد طلب تحقق إيداع جديد 🚨",
        )
    )


async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await send_to_check_deposit(update=update, context=context)
        await update.message.reply_text(
            text=THANK_YOU_TEXT,
            reply_markup=build_user_keyboard(),
        )

        return ConversationHandler.END
