from telegram import (
    Update,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from common.common import (
    build_user_keyboard,
    payment_method_pattern,
    build_back_button,
    build_methods_keyboard,
    format_amount,
    send_to_photos_archive,
)

from common.decorators import (
    check_if_user_present_decorator,
    check_user_call_on_or_off_decorator,
    check_user_pending_orders_decorator,
)
from common.force_join import check_if_user_member_decorator
from common.back_to_home_page import (
    back_to_user_home_page_handler,
    back_to_user_home_page_button,
)

from start import start_command

from models import BuyUsdtdOrder, PaymentMethod, Photo
from constants import *

import os

(
    USDT_TO_BUY_AMOUNT,
    YES_NO_BUY_USDT,
    BUY_USDT_METHOD,
    BANK_NUMBER_BUY_USDT,
    CASH_CODE,
    BANK_ACCOUNT_NAME_BUY_USDT,
    BUY_USDT_CHECK,
) = range(7)


@check_user_pending_orders_decorator
@check_user_call_on_or_off_decorator
@check_if_user_present_decorator
@check_if_user_member_decorator
async def buy_usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        text = (
            f"<b>1 USDT = {context.bot_data['data']['usdt_to_syp']} SYP</b>\n\n"
            "كم تريد أن تبيع؟💵"
        )
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(back_to_user_home_page_button),
        )
        return USDT_TO_BUY_AMOUNT


async def usdt_to_buy_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_usdt_to_buy_amount"),
            back_to_user_home_page_button[0],
        ]
        if update.message:
            amount = float(update.message.text)

            if amount <= 0:
                await update.message.reply_text(
                    text="الرجاء إرسال عدد موجب لا يساوي الصفر",
                    reply_markup=InlineKeyboardMarkup(back_buttons),
                )
                return

            context.user_data["usdt_to_buy_amount"] = amount
        else:
            amount = context.user_data["usdt_to_buy_amount"]

        keyboard = [
            [
                InlineKeyboardButton(text="موافق 👍", callback_data="yes busdt"),
                InlineKeyboardButton(text="غير موافق 👎", callback_data="no busdt"),
            ],
            *back_buttons,
        ]
        text = (
            f"الكمية المرسلة تساوي:\n\n"
            f"<b>{amount} USDT = {format_amount(amount * context.bot_data['data']['usdt_to_syp'])} SYP</b>\n\n"
            "هل أنت موافق؟"
        )
        if update.message:
            await update.message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        return YES_NO_BUY_USDT


back_to_usdt_to_buy_amount = buy_usdt


async def yes_no_buy_usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if update.callback_query.data.startswith("no"):
            await update.callback_query.answer("حسناً، تم الإلغاء")
            await update.callback_query.edit_message_text(
                text=HOME_PAGE_TEXT,
                reply_markup=build_user_keyboard(),
            )
            return ConversationHandler.END
        else:
            buy_usdt_methods = build_methods_keyboard(buy_usdt=True)
            buy_usdt_methods.append(build_back_button("back_to_yes_no_busdt"))
            buy_usdt_methods.append(back_to_user_home_page_button[0])
            await update.callback_query.edit_message_text(
                text="اختر وسيلة الدفع لاستلام أموالك 💳",
                reply_markup=InlineKeyboardMarkup(buy_usdt_methods),
            )
            return BUY_USDT_METHOD


back_to_yes_no_buy_usdt = usdt_to_buy_amount


async def buy_usdt_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        data = update.callback_query.data
        if not data.startswith("back"):
            method = PaymentMethod.get_payment_method(name=data)

            if method.on_off == 0:
                await update.callback_query.answer("هذه الوسيلة متوقفة مؤقتاً ❗️")
                return

            context.user_data["payment_method_buy_usdt"] = data

        back_keyboard = [
            build_back_button("back_to_busdt_method"),
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text=f"أرسل رقم حساب {data}",
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        if context.user_data["payment_method_buy_usdt"] in [BEMO, BARAKAH]:
            return BANK_NUMBER_BUY_USDT
        return CASH_CODE


back_to_buy_usdt_method = yes_no_buy_usdt


async def bank_number_buy_usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_keyboard = [
            build_back_button("back_to_bank_number_busdt"),
            back_to_user_home_page_button[0],
        ]
        if update.message:
            context.user_data["payment_method_number_buy_usdt"] = update.message.text
            await update.message.reply_text(
                text="أرسل اسم صاحب الحساب كما هو مسجل بالبنك.",
                reply_markup=InlineKeyboardMarkup(back_keyboard),
            )
        else:
            await update.callback_query.edit_message_text(
                text="أرسل اسم صاحب الحساب كما هو مسجل بالبنك.",
                reply_markup=InlineKeyboardMarkup(back_keyboard),
            )

        return BANK_ACCOUNT_NAME_BUY_USDT


back_to_bank_number_buy_usdt = buy_usdt_method


async def cash_code_bank_account_name_buy_usdt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE:

        if context.user_data["payment_method_buy_usdt"] not in (
            BARAKAH,
            BEMO,
        ):
            context.user_data["payment_method_number_buy_usdt"] = update.message.text
            context.user_data["bank_account_name_buy_usdt"] = ""

        else:
            context.user_data["bank_account_name_buy_usdt"] = update.message.text

        back_keyboard = [
            build_back_button(
                "back_to_cash_code_busdt"
                if context.user_data["payment_method_buy_usdt"] not in [BEMO, BARAKAH]
                else "back_to_bank_account_name_busdt"
            ),
            back_to_user_home_page_button[0],
        ]
        text = (
            f"أرسل الآن العملات إلى المحفظة:\n\n"
            f"<code>{context.bot_data['data']['USDT_number']}</code>\n\n"
            "ثم أرسل لقطة شاشة لعملية الدفع إلى البوت لنقوم بتوثيقها.\n\n"
            "<b>ملاحظة هامة: الشبكة المستخدمه هي TRC20</b>"
        )
        await update.message.reply_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )

        return BUY_USDT_CHECK


back_to_cash_code_buy_usdt = buy_usdt_method
back_to_bank_account_name_buy_usdt = bank_number_buy_usdt


async def buy_usdt_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        method = context.user_data["payment_method_buy_usdt"]
        method_info = ""

        method_info = f"<b>Payment info</b>: <code>{context.user_data['payment_method_number_buy_usdt']}</code>"
        method_info += (
            f"\nاسم صاحب الحساب: <b>{context.user_data['bank_account_name_buy_usdt']}</b>"
            if method in [BARAKAH, BEMO]
            else ""
        )

        serial = await BuyUsdtdOrder.add_buy_usdt_order(
            group_id=context.bot_data["data"]["buy_usdt_orders_group"],
            user_id=update.effective_user.id,
            method=method,
            amount=context.user_data["usdt_to_buy_amount"],
            payment_method_number=context.user_data["payment_method_number_buy_usdt"],
            bank_account_name=context.user_data["bank_account_name_buy_usdt"],
        )

        message = await context.bot.send_photo(
            chat_id=context.bot_data["data"]["buy_usdt_orders_group"],
            photo=update.message.photo[-1],
            caption=stringify_order(
                context.user_data["usdt_to_buy_amount"],
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
        await send_to_photos_archive(
            context=context,
            photo=update.message.photo[-1],
            order_type="buy_usdt",
            serial=serial,
        )
        await BuyUsdtdOrder.add_message_ids(
            serial=serial,
            pending_check_message_id=message.id,
        )
        await update.message.reply_text(
            text="شكراً لك، تم إرسال طلبك إلى قسم المراجعة، سيصلك رد خلال وقت قصير.",
            reply_markup=build_user_keyboard(),
        )
        return ConversationHandler.END


def stringify_order(amount, method, serial, method_info):
    return (
        f"طلب شراء USDT جديد:\n\n"
        f"المبلغ💵: <code>{amount}</code> USDT\n"
        f"وسيلة الدفع 💳: <b>{method}</b>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        f"{method_info}\n"
    )


buy_usdt_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(buy_usdt, "^busdt$")],
    states={
        USDT_TO_BUY_AMOUNT: [
            MessageHandler(
                filters=filters.Regex("^[1-9]+\.?\d*$"), callback=usdt_to_buy_amount
            )
        ],
        YES_NO_BUY_USDT: [
            CallbackQueryHandler(yes_no_buy_usdt, "^yes busdt$|^no busdt$")
        ],
        BUY_USDT_METHOD: [
            CallbackQueryHandler(buy_usdt_method, payment_method_pattern)
        ],
        BANK_NUMBER_BUY_USDT: [
            MessageHandler(
                filters=filters.Regex(".*") & ~filters.COMMAND,
                callback=bank_number_buy_usdt,
            )
        ],
        CASH_CODE: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=cash_code_bank_account_name_buy_usdt,
            )
        ],
        BANK_ACCOUNT_NAME_BUY_USDT: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=cash_code_bank_account_name_buy_usdt,
            )
        ],
        BUY_USDT_CHECK: [
            MessageHandler(filters=filters.PHOTO, callback=buy_usdt_check)
        ],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_buy_usdt_method, "^back_to_busdt_method$"),
        CallbackQueryHandler(back_to_yes_no_buy_usdt, "^back_to_yes_no_busdt$"),
        CallbackQueryHandler(
            back_to_bank_number_buy_usdt, "^back_to_bank_number_busdt$"
        ),
        CallbackQueryHandler(
            back_to_bank_account_name_buy_usdt, "^back_to_bank_account_name_busdt$"
        ),
        CallbackQueryHandler(
            back_to_cash_code_buy_usdt, "^back_to_cash_code_busdt$"
        ),
        CallbackQueryHandler(
            back_to_usdt_to_buy_amount, "^back_to_usdt_to_buy_amount$"
        ),
        back_to_user_home_page_handler,
        start_command,
    ],
    name="buy_usdt_handler",
    persistent=True,
)
