from telegram import (
    Update,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes, CallbackQueryHandler


async def back_to_check_agent_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        data = update.callback_query.data.split("_")
        manager_id = int(data[-2])
        if update.effective_user.id != manager_id:
            await update.callback_query.answer(
                text="شخص آخر يعمل على هذا الطلب.",
                show_alert=True,
            )
            return
        serial = int(data[-1])
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_row(
                [
                    InlineKeyboardButton(
                        text="قبول ✅",
                        callback_data=f"accept_agent_order_{serial}",
                    ),
                    InlineKeyboardButton(
                        text="رفض ❌",
                        callback_data=f"decline_agent_order_{serial}",
                    ),
                ]
            ),
        )


back_to_check_agent_order_handler = CallbackQueryHandler(
    back_to_check_agent_order,
    "^back_from_((decline)|(accept))_trusted_agent_order$",
)
