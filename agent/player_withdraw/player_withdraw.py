from telegram import (
    Update,
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
    build_agent_keyboard,
    build_methods_keyboard,
    payment_method_pattern,
    build_back_button,
)

from common.back_to_home_page import (
    back_to_agent_home_page_button,
    back_to_agent_home_page_handler,
)
from agent.player_deposit.player_deposit import player_deposit
from user.withdraw.common import send_withdraw_order_to_check
from start import agent_command, start_command
from models import PaymentMethod
from constants import *
import os

(
    WITHDRAW_ACCOUNT,
    PAYMENT_METHOD,
    PAYMENT_INFO,
    BANK_ACCOUNT_NAME,
    WITHDRAW_CODE,
) = range(5)


player_withdraw = player_deposit


async def get_player_number_withdraw(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE:
        payment_methods = build_methods_keyboard()
        payment_methods.append(build_back_button("back_to_get_player_number_withdraw"))
        payment_methods.append(back_to_agent_home_page_button[0])
        if update.message:
            context.user_data["withdraw_account"] = update.message.text
            await update.message.reply_text(
                text="اختر وسيلة الدفع 💳",
                reply_markup=InlineKeyboardMarkup(payment_methods),
            )
        else:
            await update.callback_query.edit_message_text(
                text="اختر وسيلة الدفع 💳",
                reply_markup=InlineKeyboardMarkup(payment_methods),
            )

        return PAYMENT_METHOD


back_to_get_player_number_withdraw = player_withdraw


async def choose_payment_method_player_withdraw(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
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
            build_back_button("back_to_choose_payment_method_player_withdraw"),
            back_to_agent_home_page_button[0],
        ]

        if context.user_data["payment_method"] == USDT:
            text = "أرسل كود محفظة USDT 👝\n\n<b>ملاحظة هامة: الشبكة المستخدمه هي TRC20</b>"
        else:
            text = f"أرسل رقم حساب {data}"

        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )

        return PAYMENT_INFO


back_to_choose_payment_method_player_withdraw = get_player_number_withdraw


async def get_withdraw_code_bank_account_name_player_withdraw(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_chat.type == Chat.PRIVATE:
        back_keyboard = [
            build_back_button("back_to_get_payment_info_player_withdraw"),
            back_to_agent_home_page_button[0],
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


back_to_get_payment_info_player_withdraw = choose_payment_method_player_withdraw


async def get_bank_accuont_name_player_withdraw(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE:
        if update.message:
            context.user_data["bank_account_name"] = update.message.text
        back_keyboard = [
            build_back_button("back_to_get_bank_account_name_player_withdraw"),
            back_to_agent_home_page_button[0],
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


back_to_get_bank_account_name_player_withdraw = (
    get_withdraw_code_bank_account_name_player_withdraw
)


async def get_withdraw_code_player_withdraw(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE:
        res = await send_withdraw_order_to_check(
            acc_number=context.user_data["withdraw_account"],
            bank_account_name=context.user_data["bank_account_name"],
            context=context,
            method=context.user_data["payment_method"],
            payment_method_number=context.user_data["payment_method_number"],
            target_group=context.bot_data["data"]["withdraw_orders_group"],
            user_id=update.effective_user.id,
            w_type="balance",
            withdraw_code=update.message.text,
            agent_id=update.effective_user.id,
        )
        if not res:
            await update.message.reply_text(
                text="لقد تم إرسال هذا الكود إلى البوت من قبل ❗️",
            )
            return

        await update.message.reply_text(
            text="شكراً لك، تم إرسال طلبك إلى قسم المراجعة، سيصلك رد خلال وقت قصير.",
            reply_markup=build_agent_keyboard(),
        )

        return ConversationHandler.END


player_withdraw_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            player_withdraw,
            "^player_withdraw$",
        ),
    ],
    states={
        WITHDRAW_ACCOUNT: [
            MessageHandler(
                filters=filters.Regex("^\d+$"), callback=get_player_number_withdraw
            ),
        ],
        PAYMENT_METHOD: [
            CallbackQueryHandler(
                choose_payment_method_player_withdraw,
                payment_method_pattern,
            )
        ],
        PAYMENT_INFO: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_withdraw_code_bank_account_name_player_withdraw,
            )
        ],
        BANK_ACCOUNT_NAME: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_bank_accuont_name_player_withdraw,
            )
        ],
        WITHDRAW_CODE: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_withdraw_code_player_withdraw,
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_get_player_number_withdraw,
            "^back_to_get_player_number_withdraw$",
        ),
        CallbackQueryHandler(
            back_to_choose_payment_method_player_withdraw,
            "^back_to_choose_payment_method_player_withdraw$",
        ),
        CallbackQueryHandler(
            back_to_get_payment_info_player_withdraw,
            "^back_to_get_payment_info_player_withdraw$",
        ),
        CallbackQueryHandler(
            back_to_get_bank_account_name_player_withdraw,
            "^back_to_get_bank_account_name_player_withdraw$",
        ),
        back_to_agent_home_page_handler,
        start_command,
        agent_command,
    ],
    name="player_withdraw_handler",
    persistent=True,
)
