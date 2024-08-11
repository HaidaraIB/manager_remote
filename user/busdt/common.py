from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import models

from common.stringifies import stringify_check_busdt_order
from common.common import send_to_media_archive
from common.constants import *

BUSDT_AMOUNT_TEXT = (
    "<b>1 USDT = {} AED</b>\n\n"
    "كم تريد أن تبيع؟ 💵\n\n"
    "How much do you wanna sell?💵"
)
SEND_POSITIVE_TEXT = (
    "الرجاء إرسال عدد موجب لا يساوي الصفر\n\n" "Please send a non-zero positive number."
)

DO_YOU_AGREE_TEXT = "<b>{} USDT = {} AED</b>\n\n" "هل أنت موافق؟\n\n" "Do you agree?"

AGREE_TEXT = "موافق 👍 - " "Agree 👍"
DISAGREE_TEXT = "غير موافق 👍 - " "Disagree 👍"

CHOOSE_METHOD_TEXT = (
    "اختر وسيلة الدفع لاستلام أموالك 💳\n\n" "Choose a payment method💳"
)


SEND_PAYMENT_INFO_TEXT = "أرسل رقم حساب {}\n\n" "Send {} account number"


SEND_MONEY_TEXT = (
    "أرسل الآن العملات إلى المحفظة:\n\n"
    "<code>{}</code>\n\n"
    "ثم أرسل لقطة شاشة أو ملف pdf لعملية الدفع إلى البوت لنقوم بتوثيقها.\n\n"
    "<b>ملاحظة هامة: الشبكة المستخدمه هي TRC20</b>\n\n"
    "Send the currencies to the address:\n\n"
    "<code>{}</code>\n\n"
    "And then provide a screenshot or a pdf for the process.\n\n"
    "<b>Pleas note that the network is TRC20</b>\n\n"
)


async def send_busdt_order_to_check(update: Update, context: ContextTypes.DEFAULT_TYPE):

    method = context.user_data["payment_method_busdt"]
    bank_account_name = context.user_data["bank_account_name_busdt"]
    aeban_number = context.user_data["aeban_number_busdt"]
    payment_method_number = context.user_data["payment_method_number_busdt"]
    method_info = f"<b>Payment info</b>: <code>{payment_method_number}</code>"
    target_group = context.bot_data["data"]["busdt_orders_group"]
    amount = context.user_data["usdt_to_buy_amount"]

    if method in AEBAN_LIST:
        method_info += (
            f"\nرقم الآيبان: <b>{aeban_number}</b>"
            + f"\nاسم صاحب الحساب: <b>{bank_account_name}</b>"
        )

    elif method not in CRYPTO_LIST:
        method_info += f"\nاسم صاحب الحساب: <b>{bank_account_name}</b>"

    serial = await models.BuyUsdtdOrder.add_busdt_order(
        group_id=target_group,
        user_id=update.effective_user.id,
        method=method,
        amount=amount,
        payment_method_number=payment_method_number,
        bank_account_name=bank_account_name,
        aeban_number=aeban_number
    )
    if update.message.photo:
        message = await context.bot.send_photo(
            chat_id=target_group,
            photo=update.message.photo[-1],
            caption=stringify_check_busdt_order(
                amount=amount,
                method=method,
                serial=serial,
                method_info=method_info,
            ),
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="التحقق ☑️", callback_data=f"check_busdt_order_{serial}"
                )
            ),
        )
        media = update.message.photo[-1]
    else:
        message = await context.bot.send_document(
            chat_id=target_group,
            document=update.message.document,
            caption=stringify_check_busdt_order(
                amount=amount,
                method=method,
                serial=serial,
                method_info=method_info,
            ),
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="التحقق ☑️", callback_data=f"check_busdt_order_{serial}"
                )
            ),
        )
        media = update.message.document
    await send_to_media_archive(
        context=context,
        media=media,
        order_type="busdt",
        serial=serial,
    )

    await models.BuyUsdtdOrder.add_message_ids(
        serial=serial,
        pending_check_message_id=message.id,
    )
