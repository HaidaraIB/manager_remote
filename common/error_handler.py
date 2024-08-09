from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TimedOut, NetworkError
import traceback
import json
import html
import os
from common.constants import *


def format_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    try:
        message = f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
    except TypeError:
        message = "<pre>update = TypeError"

    message += (
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )
    return message


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    if isinstance(context.error, (TimedOut, NetworkError)):
        return
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    try:
        error = f"update = {json.dumps(update_str, indent=2, ensure_ascii=False)}\n\n"

    except TypeError:
        error = "update = TypeError\n\n"

    error += (
        f"user_data = {str(context.user_data)}\n"
        f"chat_data = {str(context.chat_data)}\n\n"
        f"{''.join(traceback.format_exception(None, context.error, context.error.__traceback__))}\n\n"
        f"{'-'*100}\n\n\n"
    )

    write_error(error)

    await context.bot.send_message(
        chat_id=int(os.getenv("ERRORS_CHANNEL")),
        text=format_error(update, context),
    )


def write_error(error: str):
    with open("errors.txt", "a", encoding="utf-8") as f:
        f.write(error)
