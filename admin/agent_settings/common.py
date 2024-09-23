from telegram import InlineKeyboardButton, Update, Chat, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from user.work_with_us.common import build_govs_keyboard
from common.common import build_back_button
from common.back_to_home_page import back_to_admin_home_page_button
from custom_filters import Admin


def build_agent_settings_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                text="حذف وكيل",
                callback_data="remove_agent",
            ),
            InlineKeyboardButton(
                text="عرض وكيل",
                callback_data="show_agent",
            ),
        ],
    ]
    return keyboard


GOV, AGENT = range(2)


async def choose_agent_settings_option(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        govs_keyboard = build_govs_keyboard()
        govs_keyboard.append(build_back_button("back_to_agent_settings"))
        govs_keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر المحافظة:", reply_markup=InlineKeyboardMarkup(govs_keyboard)
        )
        return GOV


