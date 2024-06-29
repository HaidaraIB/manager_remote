from telegram import (
    Update,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from common.common import (
    build_user_keyboard,
    build_methods_keyboard,
    payment_method_pattern,
    check_if_user_created_account_from_bot_decorator,
    check_if_user_present_decorator,
    build_back_button,
)

from common.force_join import check_if_user_member_decorator
from common.back_to_home_page import (
    back_to_user_home_page_handler,
    back_to_user_home_page_button,
)

from start import start_command
from DB import DB

(
    DEPOSIT_AMOUNT,
    ACCOUNT_DEPOSIT,
    DEPOSIT_METHOD,
    SEND_TO_CHECK_DEPOSIT,
) = range(4)


@check_if_user_present_decorator
@check_if_user_member_decorator
@check_if_user_created_account_from_bot_decorator
async def make_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not context.bot_data["data"]["user_calls"]["deposit"]:
            await update.callback_query.answer("الإيداعات متوقفة حالياً❗️")
            return ConversationHandler.END

        await update.callback_query.edit_message_text(
            text="أرسل المبلغ الذي تريد إيداعه💵",
            reply_markup=InlineKeyboardMarkup(back_to_user_home_page_button),
        )
        return DEPOSIT_AMOUNT


async def deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        accounts = DB.get_user_accounts(user_id=update.effective_user.id)
        accounts_keyboard = [
            InlineKeyboardButton(
                text=a["acc_num"],
                callback_data=str(a["acc_num"]),
            )
            for a in accounts
        ]
        keybaord = [
            accounts_keyboard,
            build_back_button("back to deposti amount"),
            back_to_user_home_page_button[0],
        ]
        if update.message:
            context.user_data["deposit_amount"] = int(update.message.text)
            await update.message.reply_text(
                text="اختر حساباً من حساباتك المسجلة لدينا",
                reply_markup=InlineKeyboardMarkup(keybaord),
            )
        else:
            await update.callback_query.edit_message_text(
                text="اختر حساباً من حساباتك المسجلة لدينا",
                reply_markup=InlineKeyboardMarkup(keybaord),
            )
        return ACCOUNT_DEPOSIT


back_to_deposit_amount = make_deposit


async def account_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not update.callback_query.data.startswith("back"):
            context.user_data["account_deposit"] = int(update.callback_query.data)
        deposit_methods = build_methods_keyboard()
        deposit_methods.append(build_back_button("back to account number deposit"))
        deposit_methods.append(back_to_user_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر وسيلة الدفع💳",
            reply_markup=InlineKeyboardMarkup(deposit_methods),
        )
        return DEPOSIT_METHOD


back_to_account_deposit = deposit_amount


async def deposit_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        data = update.callback_query.data
        method = DB.get_payment_method(name=data)
        if method[1] == 0:
            await update.callback_query.answer("هذه الوسيلة متوقفة مؤقتاً❗️")
            return
        context.user_data["deposit_method"] = data
        back_buttons = [
            build_back_button("back to deposit method"),
            back_to_user_home_page_button[0],
        ]
        text = (
            f"قم بإرسال المبلغ المراد إيداعه إلى:\n\n"
            f"<code>{context.bot_data['data'][f'{data}_number']}</code>\n\n"
            f"ثم أرسل لقطة شاشة لعملية الدفع إلى البوت لنقوم بتوثيقها.\n\n"
        )
        if data == "USDT":
            text += "<b>ملاحظة هامة: الشبكة المستخدمه هي TRC20</b>\n"

        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return SEND_TO_CHECK_DEPOSIT


back_to_deposit_method = account_deposit


async def send_to_check_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        approval_screenshot = update.message.photo[-1]

        serial = await DB.add_deposit_order(
            user_id=update.effective_user.id,
            method=context.user_data["deposit_method"],
            acc_number=context.user_data["account_deposit"],
            amount=context.user_data["deposit_amount"],
            group_id=context.bot_data["data"]["deposit_orders_group"],
        )

        message = await context.bot.send_photo(
            chat_id=context.bot_data["data"]["deposit_orders_group"],
            photo=approval_screenshot,
            caption=stringify_order(
                amount=context.user_data["deposit_amount"],
                method=context.user_data["deposit_method"],
                account_number=context.user_data["account_deposit"],
                serial=serial,
            ),
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="التحقق☑️", callback_data=f"check_deposit_{serial}"
                )
            ),
        )

        await DB.add_message_ids(
            order_type="deposit",
            serial=serial,
            pending_check_message_id=message.id,
        )
        await update.message.reply_text(
            text="شكراً لك، سيتم التحقق من الصورة وإضافة المبلغ المودع خلال وقت قصير.",
            reply_markup=build_user_keyboard(),
        )
        return ConversationHandler.END


def stringify_order(
    amount: float,
    method: str,
    account_number: int,
    serial: int,
):
    return (
        "إيداع جديد:\n"
        f"المبلغ: <code>{amount}</code>\n"
        f"وسيلة الدفع: <code>{method}</code>\n"
        f"رقم الحساب: <code>{account_number}</code>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        "ملاحظة: تأكد من تطابق المبلغ في الرسالة مع الذي في لقطة الشاشة لأن ما سيضاف في حالة التأكيد هو الذي في الرسالة."
    )


deposit_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(make_deposit, "^deposit$")],
    states={
        DEPOSIT_AMOUNT: [
            MessageHandler(
                filters=filters.Regex("^[1-9]+\.?\d*$"), callback=deposit_amount
            )
        ],
        ACCOUNT_DEPOSIT: [CallbackQueryHandler(account_deposit, "^\d+$")],
        DEPOSIT_METHOD: [CallbackQueryHandler(deposit_method, payment_method_pattern)],
        SEND_TO_CHECK_DEPOSIT: [
            MessageHandler(filters=filters.PHOTO, callback=send_to_check_deposit)
        ],
    },
    fallbacks=[
        start_command,
        back_to_user_home_page_handler,
        CallbackQueryHandler(back_to_deposit_amount, "^back to deposit amount$"),
        CallbackQueryHandler(back_to_deposit_method, "^back to deposit method$"),
        CallbackQueryHandler(
            back_to_account_deposit, "^back to account number deposit$"
        ),
    ],
    name="deposit_handler",
    persistent=True,
)
