from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Chat,
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
    build_back_button,
)

from common.decorators import (
    check_if_user_created_account_from_bot_decorator,
    check_if_user_present_decorator,
    check_user_call_on_or_off_decorator,
    check_user_pending_orders_decorator,
)

from common.force_join import check_if_user_member_decorator
from common.back_to_home_page import (
    back_to_user_home_page_handler,
    back_to_user_home_page_button,
)
from user.withdraw.common import send_withdraw_order_to_check
from start import start_command
from models import PaymentMethod, Account
from constants import *
import os

(
    WITHDRAW_ACCOUNT,
    PAYMENT_METHOD,
    PAYMENT_INFO,
    BANK_ACCOUNT_NAME,
    WITHDRAW_CODE,
) = range(5)


@check_user_pending_orders_decorator
@check_user_call_on_or_off_decorator
@check_if_user_present_decorator
@check_if_user_member_decorator
@check_if_user_created_account_from_bot_decorator
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
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
            text="اختر حساباً من حساباتك المسجلة لدينا",
            reply_markup=InlineKeyboardMarkup(keybaord),
        )
        return WITHDRAW_ACCOUNT


async def choose_withdraw_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not update.callback_query.data.startswith("back"):
            context.user_data["withdraw_account"] = update.callback_query.data
        payment_methods = build_methods_keyboard()
        payment_methods.append(build_back_button("back_to_choose_withdraw_account"))
        payment_methods.append(back_to_user_home_page_button[0])

        await update.callback_query.edit_message_text(
            text="اختر وسيلة الدفع 💳",
            reply_markup=InlineKeyboardMarkup(payment_methods),
        )
        return PAYMENT_METHOD


back_to_choose_withdraw_account = withdraw


async def choose_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        if not update.callback_query.data.startswith("back"):
            data = update.callback_query.data
            method = PaymentMethod.get_payment_method(name=data)
            if not method.on_off:
                await update.callback_query.answer("هذه الوسيلة متوقفة مؤقتاً❗️")
                return

            context.user_data["payment_method"] = data
        else:
            data = context.user_data["payment_method"]

        back_keyboard = [
            build_back_button("back_to_choose_payment_method"),
            back_to_user_home_page_button[0],
        ]

        if context.user_data["payment_method"] == USDT:
            text = "أرسل كود محفظتك👝\n\n<b>ملاحظة هامة: الشبكة المستخدمه هي TRC20</b>"
        else:
            text = f"أرسل رقم حساب {data}"

        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )

        return PAYMENT_INFO


back_to_choose_payment_method = choose_withdraw_account


async def get_withdraw_code_bank_account_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_chat.type == Chat.PRIVATE:
        back_keyboard = [
            build_back_button("back_to_get_payment_info"),
            back_to_user_home_page_button[0],
        ]
        if context.user_data["payment_method"] in (BARAKAH, BEMO):
            if update.message:
                await update.message.reply_text(
                    text="أرسل اسم صاحب الحساب كما هو مسجل بالبنك.",
                    reply_markup=InlineKeyboardMarkup(back_keyboard),
                )
            else:
                await update.callback_query.edit_message_text(
                    text="أرسل اسم صاحب الحساب كما هو مسجل بالبنك.",
                    reply_markup=InlineKeyboardMarkup(back_keyboard),
                )
            return BANK_ACCOUNT_NAME

        context.user_data["payment_method_number"] = update.message.text
        context.user_data["bank_account_name"] = ""

        await update.message.reply_video(
            video=os.getenv("VIDEO_ID"),
            filename="how_to_get_withdraw_code",
            caption=(
                "أرسل كود السحب\n\n" "يوضح الفيديو المرفق كيفية الحصول على الكود."
            ),
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return WITHDRAW_CODE


back_to_get_payment_info = choose_payment_method


async def get_bank_accuont_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if update.message:
            context.user_data["bank_account_name"] = update.message.text
        back_keyboard = [
            build_back_button("back_to_bank_account_name"),
            back_to_user_home_page_button[0],
        ]
        await update.message.reply_video(
            video=os.getenv("VIDEO_ID"),
            filename="how_to_get_withdraw_code",
            caption=(
                "أرسل كود السحب\n\n" "يوضح الفيديو المرفق كيفية الحصول على الكود."
            ),
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return WITHDRAW_CODE


back_to_bank_account_name = get_withdraw_code_bank_account_name


async def get_withdraw_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        res = await send_withdraw_order_to_check(
            acc_number=context.user_data["withdraw_account"],
            bank_account_name=context.user_data["bank_account_name"],
            context=context,
            method=context.user_data["payment_method"],
            payment_method_number=context.user_data["payment_method_number"],
            target_group=context.bot_data["data"]["withdraw_orders_group"],
            user_id=update.effective_user.id,
            w_type=context.user_data.get("withdraw_type", "balance"),
            withdraw_code=update.message.text,
        )
        if not res:
            await update.message.reply_text(
                text="لقد تم إرسال هذا الكود إلى البوت من قبل ❗️",
            )
            return

        await update.message.reply_text(
            text="شكراً لك، تم إرسال طلبك إلى قسم المراجعة، سيصلك رد خلال وقت قصير.",
            reply_markup=build_user_keyboard(),
        )

        return ConversationHandler.END


withdraw_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            choose_withdraw_account,
            "^withdraw$",
        ),
    ],
    states={
        WITHDRAW_ACCOUNT: [
            CallbackQueryHandler(
                choose_withdraw_account,
                "^\d+$",
            ),
        ],
        PAYMENT_METHOD: [
            CallbackQueryHandler(
                choose_payment_method,
                payment_method_pattern,
            )
        ],
        PAYMENT_INFO: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_withdraw_code_bank_account_name,
            )
        ],
        BANK_ACCOUNT_NAME: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_bank_accuont_name,
            )
        ],
        WITHDRAW_CODE: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_withdraw_code,
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_choose_withdraw_account,
            "^back_to_choose_withdraw_account$",
        ),
        CallbackQueryHandler(
            back_to_choose_payment_method,
            "^back_to_choose_payment_method$",
        ),
        CallbackQueryHandler(
            back_to_get_payment_info,
            "^back_to_get_payment_info$",
        ),
        CallbackQueryHandler(
            back_to_bank_account_name,
            "^back_to_bank_account_name$",
        ),
        back_to_user_home_page_handler,
        start_command,
    ],
    name="withdraw_handler",
    persistent=True,
)
