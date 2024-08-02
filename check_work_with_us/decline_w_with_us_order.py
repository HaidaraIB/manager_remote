from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Chat,
)

from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from user.work_with_us.common import syrian_govs_en_ar
from custom_filters import Declined, AgentOrder
import models


async def decline_agent_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        data = update.callback_query.data.split("_")
        serial = int(data[-1])
        role = data[-2]
        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بسبب الرفض",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن رفض الطلب 🔙",
                    callback_data=f"back_from_decline_{role}_{update.effective_user.id}_{serial}",
                )
            )
        )


async def get_decline_agent_order_reason(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data.split("_")

        serial = int(data[-1])
        order = models.WorkWithUsOrder.get_one_order(serial=serial)

        await models.WorkWithUsOrder.decline_work_with_us_order(
            serial=serial, reason=update.message.text
        )
        await context.bot.send_message(
            chat_id=order.user_id,
            text=(
                f"عذراً، تم رفض طلبك للعمل معنا كوكيل لمحافظة <b>{syrian_govs_en_ar[order.gov]}</b>\n\n"
                "السبب:\n"
                f"{update.message.text_html}\n\n"
                f"الرقم التسلسلي للطلب: <code>{serial}</code>"
            ),
        )
        await update.message.reply_to_message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تم الرفض ❌",
                    callback_data="تم الرفض ❌",
                )
            )
        )


decline_agent_order_handler = CallbackQueryHandler(
    decline_agent_order, "^decline_((agent)|(partner))_\d+$"
)

get_decline_agent_order_reason_handler = MessageHandler(
    filters=AgentOrder() & Declined() & filters.REPLY & filters.TEXT & ~filters.COMMAND,
    callback=get_decline_agent_order_reason,
)
