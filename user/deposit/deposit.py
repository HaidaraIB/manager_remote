from telegram import (
    Update,
    Chat,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from common.constants import *
from common.common import (
    build_user_keyboard,
    payment_method_pattern,
    build_back_button,
)

from common.back_to_home_page import (
    back_to_user_home_page_handler,
    back_to_user_home_page_button,
)
from start import start_command
from models import PaymentMethod
from user.deposit.common import (
    ACCOUNT_DEPOSIT,
    DEPOSIT_METHOD,
    account_deposit,
    send_to_check_deposit,
    make_deposit,
    back_to_account_deposit,
)
from user.deposit.bemo_deposit import (
    DEPOSIT_AMOUNT,
    BEMO_REF_NUM,
    bemo_deposit,
    get_deposit_amount,
    back_to_deposit_amount,
)


REF_NUM = 2


async def deposit_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        method_name = update.callback_query.data
        method = PaymentMethod.get_payment_method(name=method_name)
        if method.on_off == 0:
            await update.callback_query.answer(
                "هذه الوسيلة متوقفة مؤقتاً❗️",
                show_alert=True,
            )
            return
        context.user_data["deposit_method"] = method_name
        context.user_data["deposit_amount"] = 0

        back_buttons = [
            build_back_button("back_to_deposit_method"),
            back_to_user_home_page_button[0],
        ]
        text = (
            f"قم بإرسال المبلغ المراد إيداعه إلى:\n\n"
            f"<code>{context.bot_data['data'][f'{method_name}_number']}</code>\n\n"
            f"ثم أرسل رقم عملية الدفع إلى البوت لنقوم بتوثيقها.\n\n"
        )
        if method_name == "USDT":
            text += "<b>ملاحظة هامة: الشبكة المستخدمه هي TRC20</b>\n"

        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return REF_NUM


back_to_deposit_method = account_deposit


async def get_ref_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        res = await send_to_check_deposit(
            context=context,
            user_id=update.effective_user.id,
            ref_num=update.message.text,
            acc_number=context.user_data["account_deposit"],
            method=context.user_data["deposit_method"],
            target_group=context.bot_data["data"]["deposit_orders_group"],
            amount=context.user_data["deposit_amount"],
        )
        if not res:
            await update.message.reply_text(
                text="رقم عملية مكرر ❗️",
            )
            return

        await update.message.reply_text(
            text="شكراً لك، سيتم التحقق من العملية وإضافة المبلغ المودع خلال وقت قصير.",
            reply_markup=build_user_keyboard(),
        )

        return ConversationHandler.END


deposit_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            make_deposit,
            "^deposit$",
        ),
    ],
    states={
        ACCOUNT_DEPOSIT: [
            CallbackQueryHandler(
                account_deposit,
                "^\d+$",
            ),
        ],
        DEPOSIT_METHOD: [
            CallbackQueryHandler(
                bemo_deposit,
                BEMO,
            ),
            CallbackQueryHandler(
                deposit_method,
                payment_method_pattern,
            ),
        ],
        REF_NUM: [
            MessageHandler(
                filters=filters.Regex("^\d+$"),
                callback=get_ref_num,
            ),
        ],
        DEPOSIT_AMOUNT: [
            MessageHandler(
                filters=filters.Regex("^\d+.?\d*$"),
                callback=get_deposit_amount,
            )
        ],
        BEMO_REF_NUM: [
            MessageHandler(
                filters=filters.Regex("^\d+$"),
                callback=get_ref_num,
            ),
        ],
    },
    fallbacks=[
        start_command,
        back_to_user_home_page_handler,
        CallbackQueryHandler(back_to_deposit_amount, "^back_to_deposit_amount$"),
        CallbackQueryHandler(back_to_deposit_method, "^back_to_deposit_method$"),
        CallbackQueryHandler(
            back_to_account_deposit, "^back_to_account_number_deposit$"
        ),
    ],
    name="deposit_handler",
    persistent=True,
)
