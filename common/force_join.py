from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
)

from telegram.constants import (
    ChatMemberStatus,
)

from common.common import build_user_keyboard
import functools
import os


def check_if_user_member_decorator(func):
    @functools.wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        is_user_member = await check_if_user_member(update=update, context=context)
        if not is_user_member:
            return ConversationHandler.END
        return await func(update, context, *args, **kwargs)

    return wrapper


async def check_if_user_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        chat_id=int(os.getenv("CHANNEL_ID")),
        user_id=update.effective_user.id,
    )
    if chat_member.status == ChatMemberStatus.LEFT:
        text = f"""لبدء استخدام البوت  يجب عليك الانضمام الى قناة البوت أولاً.
        
✅ اشترك أولاً 👇.
🔗 {os.getenv("CHANNEL_LINK")}

ثم اضغط تحقق✅"""
        check_joined_button = [
            [InlineKeyboardButton(text="تحقق✅", callback_data="check joined")]
        ]
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=text, reply_markup=InlineKeyboardMarkup(check_joined_button)
            )
        else:
            await update.message.reply_text(
                text=text, reply_markup=InlineKeyboardMarkup(check_joined_button)
            )
        return False
    return True


async def check_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_memeber = await context.bot.get_chat_member(
        chat_id=int(os.getenv("CHANNEL_ID")),
        user_id=update.effective_user.id,
    )
    if chat_memeber.status == ChatMemberStatus.LEFT:
        await update.callback_query.answer(
            text="قم بالاشتراك في الغروب أولاً",
            show_alert=True,
        )
        return

    await update.callback_query.edit_message_text(
        text="أهلاً بك...",
        reply_markup=build_user_keyboard(),
    )


check_joined_handler = CallbackQueryHandler(
    callback=check_joined, pattern="^check joined$"
)
