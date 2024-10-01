from telegram import Update, Chat
from telegram.ext import ContextTypes, MessageHandler, filters
from custom_filters import Worker, Admin
from common.common import resolve_message, send_resolved_message
import os


async def contact_dev(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or Worker().filter(update)
    ):
        msg = update.message
        if msg and (
            not (msg.text or msg.caption)
            or (msg.text and (not msg.text.startswith("/dev") or msg.text == "/dev"))
            or (msg.caption and not msg.caption.startswith("/dev"))
        ):
            return

        dev_id = int(os.getenv("DEV_ID"))
        media, media_type = resolve_message(msg)
        base_text = f"رسالة من {update.effective_user.mention_html()}:\n\n"
        text = (
            base_text + msg.text.replace("/dev", "")
            if msg.text
            else (
                base_text + msg.caption.replace("/dev", "")
                if msg.caption
                else base_text
            )
        )
        await send_resolved_message(
            media=media,
            media_type=media_type,
            context=context,
            text=text,
            chat_id=dev_id,
        )
        await msg.reply_text(text="تم ✅")


contact_dev_handler = MessageHandler(
    filters=filters.COMMAND
    | filters.PHOTO
    | filters.CAPTION
    | filters.VIDEO
    | filters.VOICE
    | filters.AUDIO,
    callback=contact_dev,
)
