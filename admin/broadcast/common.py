from telegram import Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from common.common import build_back_button
from common.back_to_home_page import back_to_admin_home_page_button


def build_broadcast_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                text="جميع المستخدمين 👥",
                callback_data="all users",
            ),
        ],
        [
            InlineKeyboardButton(
                text="مستخدمين محددين 👤",
                callback_data="specific users",
            ),
        ],
        [
            InlineKeyboardButton(
                text="الوكلاء",
                callback_data="agents",
            ),
        ],
        build_back_button("back_to_the_message"),
        back_to_admin_home_page_button[0],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_done_button():
    done_button = [
        [
            InlineKeyboardButton(
                text="تم الانتهاء 👍",
                callback_data="done entering users",
            )
        ],
        build_back_button("back_to_send_to"),
        back_to_admin_home_page_button[0],
    ]
    return InlineKeyboardMarkup(done_button)


async def send_to(user_ids: list, context: ContextTypes.DEFAULT_TYPE):
    msg: Message = context.user_data["the message"]
    for i in user_ids:
        try:
            if msg.photo:
                await context.bot.send_photo(
                    chat_id=i,
                    photo=msg.photo[-1],
                    caption=msg.caption,
                )
            elif msg.video:
                await context.bot.send_video(
                    chat_id=i,
                    video=msg.video,
                    caption=msg.caption,
                )
            else:
                await context.bot.send_message(
                    chat_id=i,
                    text=msg.text,
                )

        except:
            continue
