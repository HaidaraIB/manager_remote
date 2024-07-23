from telegram import (
    Chat,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonRequestUsers,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from telegram.error import TelegramError

from common.back_to_home_page import (
    back_to_admin_home_page_handler,
    back_to_admin_home_page_button,
)

from start import admin_command, start_command
from models import PaymentAgent, DepositAgent, Checker
from custom_filters import Admin
from admin.workers_settings.common import (
    build_positions_keyboard,
)
from constants import *

(
    WORKER_ID,
    POSITION,
) = range(2)


async def worker_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        worker_settings_keyboard = [
            [
                InlineKeyboardButton(text="إضافة موظف➕", callback_data="add worker"),
                InlineKeyboardButton(text="حذف موظف✖️", callback_data="remove worker"),
            ],
            [
                InlineKeyboardButton(
                    text="عرض الموظفين🔍", callback_data="show worker"
                ),
            ],
            [
                InlineKeyboardButton(text="رصيد 💰", callback_data="balance worker"),
            ],
            back_to_admin_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="هل تريد:", reply_markup=InlineKeyboardMarkup(worker_settings_keyboard)
        )


async def add_worker_cp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        await update.callback_query.answer()
        text = "اختر حساب الموظف الذي تريد إضافته بالضغط على الزر أدناه، يمكنك إلغاء العملية بالضغط على /admin."

        await update.callback_query.delete_message()
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=text,
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(
                            text="اختيار حساب موظف🧑🏻‍💻",
                            request_users=KeyboardButtonRequestUsers(
                                request_id=4, user_is_bot=False
                            ),
                        )
                    ]
                ],
                resize_keyboard=True,
            ),
        )
        return WORKER_ID


async def worker_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        try:
            if update.effective_message.users_shared:
                user_id = update.effective_message.users_shared.users[0].user_id
            else:
                user_id = int(update.message.text)
            worker_to_add = await context.bot.get_chat(chat_id=user_id)
        except TelegramError:
            await update.message.reply_text(
                text=(
                    "لم يتم العثور على الحساب ❗️\n\n"
                    "تأكد من أن الموظف قد بدأ محادثة مع البوت، يمكنك إلغاء العملية بالضغط على /admin."
                ),
            )
            return
        context.user_data["worker_to_add"] = worker_to_add

        await update.message.reply_text(
            text="تم العثور على الحساب✅",
            reply_markup=ReplyKeyboardRemove(),
        )
        await update.message.reply_text(
            text="اختر الوظيفة:\n\nللإنهاء اضغط /admin",
            reply_markup=build_positions_keyboard(op="add"),
        )
        return POSITION


async def position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        worker_to_add: Chat = context.user_data["worker_to_add"]
        pos = update.callback_query.data.split("_")[1]
        if pos == "deposit after check":
            await DepositAgent.add_worker(
                worker_id=worker_to_add.id,
                name=worker_to_add.full_name,
                username=worker_to_add.username,
            )
        elif pos in ["deposit", "withdraw", "buy"]:
            await Checker.add_worker(
                worker_id=worker_to_add.id,
                name=worker_to_add.full_name,
                username=worker_to_add.username,
                check_what=pos,
            )
        else:
            await PaymentAgent.add_worker(
                worker_id=worker_to_add.id,
                name=worker_to_add.full_name,
                username=worker_to_add.username,
                method=pos,
            )
        await update.callback_query.answer("تمت إضافة الموظف بنجاح✅")
        await update.callback_query.edit_message_text(
            text="تمت إضافة الموظف بنجاح✅\n\n\nاختر وظيفة أخرى إن إردت، للإنهاء اضغط /admin.",
            reply_markup=build_positions_keyboard(op="add"),
        )


back_to_worker_id = add_worker_cp

add_worker_cp_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_worker_cp, "^add worker$")],
    states={
        WORKER_ID: [
            MessageHandler(
                filters=filters.StatusUpdate.USER_SHARED,
                callback=worker_id,
            ),
            MessageHandler(
                filters=filters.Regex("^\d+$"),
                callback=worker_id,
            ),
        ],
        POSITION: [
            CallbackQueryHandler(
                position,
                "^add.+((worker)|(checker))",
            ),
        ],
    },
    fallbacks=[
        back_to_admin_home_page_handler,
        admin_command,
        start_command,
        CallbackQueryHandler(back_to_worker_id, "^back_to_worker_id$"),
    ],
)
