from telegram import (
    Update,
    Chat,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes, CallbackQueryHandler
from user.work_with_us.common import build_agent_work_with_us_keyboard


def create_promo_code_invalid_foramt_login_info():
    res = (
        "تنسيق خاطئ الرجاء الالتزام بالقالب التالي:\n\n"
        "<code>Username : \n"
        "Password : </code>\n\n"
        "مثال:\n"
        "Username : asdfasdf\n"
        "Password : sdafasdg"
        ""
    )
    return res


def create_team_cash_invalid_foramt_login_info():
    res = (
        "تنسيق خاطئ الرجاء الالتزام بالقالب التالي:\n\n"
        "<code>User ID : \n"
        "Password : \n"
        "Workplace ID : </code>\n\n"
        "مثال:\n"
        "User ID : efe3adf\n"
        "Password : sadfaf3\n"
        "Workplace ID : 12312"
        ""
    )
    return res


async def back_to_check_agent_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        data = update.callback_query.data.split("_")
        serial = int(data[-1])
        role = data[-3]
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                build_agent_work_with_us_keyboard(serial, role)
            ),
        )


back_to_check_agent_order_handler = CallbackQueryHandler(
    back_to_check_agent_order,
    "^back_from_((decline)|(accept))_((agent)|(partner))",
)
