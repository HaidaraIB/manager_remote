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
from jobs import check_deposit
from DB import DB
from custom_filters import Ref

(
    ACCOUNT_DEPOSIT,
    DEPOSIT_METHOD,
    SEND_TO_CHECK_DEPOSIT,
) = range(3)


@check_if_user_present_decorator
@check_if_user_member_decorator
@check_if_user_created_account_from_bot_decorator
async def make_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not context.bot_data["data"]["user_calls"]["deposit"]:
            await update.callback_query.answer("الإيداعات متوقفة حالياً❗️")
            return ConversationHandler.END

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


back_to_account_deposit = make_deposit


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
            f"ثم أرسل رقم عملية الدفع إلى البوت لنقوم بتوثيقها.\n\n"
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
        ref_num = update.message.text

        ref_present = DB.get_ref_number(
            number=ref_num,
            method=context.user_data["deposit_method"],
        )
        if ref_present and ref_present["order_serial"] != -1:
            await update.message.reply_text(
                text="رقم عملية مكرر!",
            )
            return

        serial = await DB.add_deposit_order(
            user_id=update.effective_user.id,
            method=context.user_data["deposit_method"],
            acc_number=context.user_data["account_deposit"],
            ref_number=ref_num,
        )

        context.job_queue.run_once(
            callback=check_deposit,
            user_id=update.effective_user.id,
            # when=120,
            when=10,
            data=serial,
            name="first_deposit_check",
            job_kwargs={
                "id": f"first_deposit_check{update.effective_user.id}",
                "misfire_grace_time": None,
                "coalesce": True,
            },
        )

        await update.message.reply_text(
            text="شكراً لك، سيتم التحقق من العملية وإضافة المبلغ المودع خلال وقت قصير.",
            reply_markup=build_user_keyboard(),
        )

        return ConversationHandler.END


async def store_ref_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if (
            not update.effective_chat.id
            == context.bot_data["data"]["deposit_orders_group"]
        ):
            return
        ref_number_info = update.message.text.split("\n")
        await DB.add_ref_number(
            number=ref_number_info[0],
            method=ref_number_info[1],
            amount=float(ref_number_info[2]),
        )


async def invalid_ref_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if (
            not update.effective_chat.id
            == context.bot_data["data"]["deposit_orders_group"]
        ):
            return
        try:
            await update.message.reply_text(
                text=(
                    "تنسيق خاطئ الرجاء الالتزام بالقالب التالي:\n\n"
                    "(رقم العملية)\n"
                    "(وسيلة الدفع)\n"
                    "(المبلغ)\n\n"
                    "قم بنسخ القالب من بين القوالب التالية لتفادي الخطأ.\n\n"
                    "<code>(رقم العملية)\n"
                    "USDT\n"
                    "(المبلغ)</code>\n\n"
                    "<code>(رقم العملية)\n"
                    "<code>PERFECT MONEY</code>\n"
                    "(المبلغ)</code>\n\n"
                    "<code>(رقم العملية)\n"
                    "<code>PAYEER</code>\n"
                    "(المبلغ)</code>\n\n"
                    "<code>(رقم العملية)\n"
                    "<code>MTN Cash🇸🇾</code>\n"
                    "(المبلغ)</code>\n\n"
                    "<code>(رقم العملية)\n"
                    "<code>Syriatel Cash🇸🇾</code>\n"
                    "(المبلغ)</code>\n\n"
                    "<code>(رقم العملية)\n"
                    "<code>بركة🇧🇭</code>\n"
                    "(المبلغ)</code>\n\n"
                    "<code>(رقم العملية)\n"
                    "<code>بيمو🇸🇦🇫🇷</code>\n"
                    "(المبلغ)</code>\n\n"
                ),
            )
        except:
            import traceback

            traceback.print_exc()


store_ref_number_handler = MessageHandler(filters=Ref(), callback=store_ref_number)
invalid_ref_format_handler = MessageHandler(filters=~Ref(), callback=invalid_ref_format)


deposit_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(make_deposit, "^deposit$")],
    states={
        ACCOUNT_DEPOSIT: [CallbackQueryHandler(account_deposit, "^\d+$")],
        DEPOSIT_METHOD: [CallbackQueryHandler(deposit_method, payment_method_pattern)],
        SEND_TO_CHECK_DEPOSIT: [
            MessageHandler(
                filters=filters.Regex("^\d+$"), callback=send_to_check_deposit
            )
        ],
    },
    fallbacks=[
        start_command,
        back_to_user_home_page_handler,
        CallbackQueryHandler(back_to_deposit_method, "^back to deposit method$"),
        CallbackQueryHandler(
            back_to_account_deposit, "^back to account number deposit$"
        ),
    ],
    name="deposit_handler",
    persistent=True,
)
