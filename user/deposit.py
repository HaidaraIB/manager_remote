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

from worker.check_deposit.check_deposit import check_deposit

from common.common import (
    build_user_keyboard,
    build_methods_keyboard,
    payment_method_pattern,
    build_back_button,
)

from common.decorators import check_if_user_created_account_from_bot_decorator, check_if_user_present_decorator
from common.force_join import check_if_user_member_decorator
from common.back_to_home_page import (
    back_to_user_home_page_handler,
    back_to_user_home_page_button,
)
from worker.check_deposit.check_deposit import stringify_order
from start import start_command
from DB import DB

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
        
        elif DB.check_user_pending_orders(
            order_type="deposit",
            user_id=update.effective_user.id,
        ):
            await update.callback_query.answer("لديك طلب إيداع قيد التنفيذ بالفعل ❗️")
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
            build_back_button("back_to_deposit_method"),
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
        order_present = DB.get_one_order(
            order_type="deposit",
            ref_num=ref_num,
        )
        if (ref_present and ref_present["order_serial"] != -1) or order_present:
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
            when=60,
            data=serial,
            name="1_deposit_check",
            job_kwargs={
                "misfire_grace_time": None,
                "coalesce": True,
            },
        )

        await context.bot.send_message(
            chat_id=context.bot_data["data"]["deposit_orders_group"],
            text=stringify_order(
                amount="لا يوجد بعد",
                account_number=context.user_data["account_deposit"],
                method=context.user_data["deposit_method"],
                serial=serial,
                ref_num=ref_num,
            ),
        )

        await update.message.reply_text(
            text="شكراً لك، سيتم التحقق من العملية وإضافة المبلغ المودع خلال وقت قصير.",
            reply_markup=build_user_keyboard(),
        )

        return ConversationHandler.END


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
        CallbackQueryHandler(back_to_deposit_method, "^back_to_deposit_method$"),
        CallbackQueryHandler(
            back_to_account_deposit, "^back_to_account_number_deposit$"
        ),
    ],
    name="deposit_handler",
    persistent=True,
)
