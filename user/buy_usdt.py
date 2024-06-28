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

from custom_filters.User import User

from common.common import (
    build_user_keyboard,
    payment_method_pattern,
    build_back_button,
    build_methods_keyboard
)

from common.force_join import check_if_user_member_decorator
from common.back_to_home_page import (
    back_to_user_home_page_handler,
    back_to_user_home_page_button,
)

from start import start_command

from DB import DB

from constants import *

(
    USDT_TO_BUY_AMOUNT,
    YES_NO_BUY_USDT,
    BUY_USDT_METHOD,
    BANK_NUMBER_BUY_USDT,
    CASH_CODE,
    BANK_ACCOUNT_NAME_BUY_USDT,
    BUY_USDT_CHECK,
) = range(7)


@check_if_user_member_decorator
async def buy_usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not context.bot_data["data"]["user_calls"]["buy_usdt"]:
            await update.callback_query.answer("شراء USDT متوقف حالياً❗️")
            return ConversationHandler.END

        user = DB.get_user(user_id=update.effective_user.id)
        if not user:
            new_user = update.effective_user
            await DB.add_new_user(
                user_id=new_user.id, username=new_user.username, name=new_user.full_name
            )

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
        context.user_data["usdt_to_buy_amount"] = int(update.message.text)
        keyboard = [
            [
                InlineKeyboardButton(text="موافق👍", callback_data="yes buy usdt"),
                InlineKeyboardButton(text="غير موافق👎", callback_data="no buy usdt"),
            ],
            build_back_button("back to usdt to buy amount"),
            back_to_user_home_page_button[0],
        ]
        text = (
            f"الكمية المرسلة تساوي:\n\n"
            f"<b>{context.user_data['usdt_to_buy_amount']} USDT = {int(context.user_data['usdt_to_buy_amount']) * context.bot_data['data']['usdt_to_syp']} SYP</b>\n\n"
            "هل أنت موافق؟"
        )

        await update.message.reply_text(
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
                text="القائمة الرئيسية🔝",
                reply_markup=build_user_keyboard(),
            )
            return ConversationHandler.END
        else:
            buy_usdt_methods = build_methods_keyboard(buy_usdt=True)
            buy_usdt_methods.append(build_back_button("back to yes no buy usdt"))
            buy_usdt_methods.append(back_to_user_home_page_button[0])
            await update.callback_query.edit_message_text(
                text="اختر وسيلة الدفع لاستلام أموالك💳",
                reply_markup=InlineKeyboardMarkup(buy_usdt_methods),
            )
            return BUY_USDT_METHOD


async def back_to_yes_no_buy_usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        keyboard = [
            [
                InlineKeyboardButton(text="موافق👍", callback_data="yes buy usdt"),
                InlineKeyboardButton(text="غير موافق👎", callback_data="no buy usdt"),
            ],
            build_back_button("back to buy usdt amount"),
            back_to_user_home_page_button[0],
        ]
        text = (
            f"الكمية المرسلة تساوي:\n\n"
            f"{context.user_data['usdt_to_buy_amount']} USDT = {int(context.user_data['usdt_to_buy_amount']) * context.bot_data['data']['usdt_to_syp']} SYP\n\n"
            "هل أنت موافق؟"
        )

        await update.callback_query.edit_message_text(
            text=text, reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return YES_NO_BUY_USDT


async def buy_usdt_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        data = update.callback_query.data
        if not data.startswith("back"):
            method = DB.get_payment_method(name=data)

            if method[1] == 0:
                await update.callback_query.answer("هذه الوسيلة متوقفة مؤقتاً❗️")
                return

            context.user_data["payment_method_buy_usdt"] = data

        back_keyboard = [
            build_back_button("back to buy usdt method"),
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text=f"أرسل رقم حساب {data}",
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        if context.user_data["payment_method_buy_usdt"] in [BEMO, BARAKAH]:
            return BANK_NUMBER_BUY_USDT
        return CASH_CODE


back_to_cash_code = back_to_bank_number_buy_usdt = buy_usdt_method


async def bank_number_buy_usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_keyboard = [
            build_back_button("back to bank number buy usdt"),
            back_to_user_home_page_button[0],
        ]
        context.user_data["payment_method_number_buy_usdt"] = update.message.text

        await update.message.reply_text(
            text="أرسل اسم صاحب الحساب كما هو مسجل بالبنك.",
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return BANK_ACCOUNT_NAME_BUY_USDT


async def back_to_bank_account_name_buy_usdt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE:
        back_keyboard = [
            build_back_button("back to bank number buy usdt"),
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="أرسل اسم صاحب الحساب كما هو مسجل بالبنك.",
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return BANK_ACCOUNT_NAME_BUY_USDT


async def back_to_buy_usdt_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        buy_usdt_methods = build_methods_keyboard(buy_usdt=True)
        buy_usdt_methods.append(build_back_button("back to yes no buy usdt"))
        buy_usdt_methods.append(back_to_user_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر وسيلة الدفع لاستلام أموالك💳",
            reply_markup=InlineKeyboardMarkup(buy_usdt_methods),
        )
        return BUY_USDT_METHOD


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
                "back to cash code buy usdt"
                if context.user_data["payment_method_buy_usdt"] not in [BEMO, BARAKAH]
                else "back to bank account name buy usdt"
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

        serial = await DB.add_buy_usdt_order(
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
                    text="التحقق☑️", callback_data=f"check_buy_usdt_order_{serial}"
                )
            ),
        )
        await DB.add_message_ids(
            order_type="buyusdt",
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
        f"وسيلة الدفع💳: <b>{method}</b>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        f"{method_info}\n"
    )


buy_usdt_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(buy_usdt, "^buy usdt$")],
    states={
        USDT_TO_BUY_AMOUNT: [
            MessageHandler(
                filters=filters.Regex("^[1-9]+\.?\d*$"), callback=usdt_to_buy_amount
            )
        ],
        YES_NO_BUY_USDT: [
            CallbackQueryHandler(yes_no_buy_usdt, "^yes buy usdt$|^no buy usdt$")
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
        CallbackQueryHandler(back_to_buy_usdt_method, "^back to buy usdt method$"),
        CallbackQueryHandler(back_to_yes_no_buy_usdt, "^back to yes no buy usdt$"),
        CallbackQueryHandler(
            back_to_bank_number_buy_usdt, "^back to bank number buy usdt$"
        ),
        CallbackQueryHandler(
            back_to_bank_account_name_buy_usdt, "^back to bank account name buy usdt$"
        ),
        CallbackQueryHandler(back_to_cash_code, "^back to cash code buy usdt$"),
        CallbackQueryHandler(
            back_to_usdt_to_buy_amount, "^back to usdt to buy amount$"
        ),
        back_to_user_home_page_handler,
        start_command,
    ],
    name="buy_usdt_handler",
    persistent=True,
)
