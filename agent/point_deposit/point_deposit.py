from telegram import Update, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from common.back_to_home_page import (
    back_to_agent_home_page_button,
    back_to_agent_home_page_handler,
)
from common.common import (
    build_back_button,
    build_agent_keyboard,
)
from agent.point_deposit.common import govs_pattern, send_to_check_deposit
from start import agent_command
import models
from custom_filters import Agent
from agent.common import agent_option, POINT

AMOUNT, REF_NUM, SCREEN_SHOT = range(1, 4)


async def choose_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Agent().filter(update):
        back_buttons = [
            build_back_button("back_to_choose_point"),
            back_to_agent_home_page_button[0],
        ]
        if not update.callback_query.data.startswith("back"):
            context.user_data["point_deposit_point"] = update.callback_query.data
        await update.callback_query.edit_message_text(
            text="أدخل المبلغ",
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return AMOUNT


back_to_choose_point = agent_option


async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Agent().filter(update):
        back_buttons = [
            build_back_button("back_to_get_amount"),
            back_to_agent_home_page_button[0],
        ]
        text = (
            f"أرسل مبلغ الإيداع إلى الرقم\n\n"
            f"<code>{context.bot_data['data']['طلبات الوكيل_number']}</code>\n\n"
            f"ثم أرسل رقم عملية الدفع إلى البوت لنقوم بتوثيقها.\n\n"
            "<b>ملاحظة: التحويل مقبول فقط من أجهزة سيريتيل أو من خطوط الجملة الخاصة لمحلات الموبايل (غير مقبول التحويل من رقم شخصي)</b>"
        )
        if not update.callback_query:
            context.user_data["point_deposit_amount"] = float(update.message.text)
            await update.message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return REF_NUM


back_to_get_amount = choose_point


async def get_ref_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Agent().filter(update):
        back_buttons = [
            build_back_button("back_to_get_ref_num"),
            back_to_agent_home_page_button[0],
        ]
        if update.message:
            t_order = models.DepositOrder.get_one_order(ref_num=update.message.text)
            if t_order:
                await update.message.reply_text(
                    text="رقم عملية مكرر!",
                )
                return
            context.user_data["point_deposit_ref_num"] = update.message.text
            await update.message.reply_text(
                text="أرسل لقطة شاشة لعملية الدفع السابقة.",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text="أرسل لقطة شاشة لعملية الدفع السابقة.",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )

        return SCREEN_SHOT


back_to_get_ref_num = get_amount


async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Agent().filter(update):

        await send_to_check_deposit(update, context)

        await update.message.reply_text(
            text="شكراً لك، تم إرسال طلبك إلى قسم المراجعة، سيصلك رد خلال وقت قصير.",
            reply_markup=build_agent_keyboard(),
        )

        return ConversationHandler.END


point_deposit_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            agent_option,
            "^point_deposit$",
        ),
    ],
    states={
        POINT: [
            CallbackQueryHandler(
                choose_point,
                govs_pattern,
            )
        ],
        AMOUNT: [
            MessageHandler(
                filters=filters.Regex("^\d+.?\d*$"),
                callback=get_amount,
            )
        ],
        REF_NUM: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_ref_num,
            )
        ],
        SCREEN_SHOT: [
            MessageHandler(
                filters=filters.PHOTO,
                callback=get_screenshot,
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_get_ref_num, "^back_to_get_ref_num$"),
        CallbackQueryHandler(back_to_get_amount, "^back_to_get_amount$"),
        CallbackQueryHandler(back_to_choose_point, "^back_to_choose_point$"),
        agent_command,
        back_to_agent_home_page_handler,
    ],
    name="point_deposit_conv",
    persistent=True,
)
