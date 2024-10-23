from telegram import (
    Chat,
    Update,
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
    WORKER_ADDED_SUCCESSFULLY_TEXT,
    CHOOSE_POSITION_TEXT,
    build_positions_keyboard,
    build_checker_positions_keyboard,
    build_deposit_after_check_positions,
)
from common.constants import *
from common.common import build_back_button

(
    WORKER_ID,
    POSITION,
    CHECK_POSITION,
    DEPOSIT_AFTER_CHECK_POSITION,
) = range(4)


async def add_worker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        text = "اختر حساب الموظف الذي تريد إضافته بالضغط على الزر أدناه، يمكنك إلغاء العملية بالضغط على /admin."

        if not update.callback_query.data.startswith("back"):
            context.user_data["worker_settings_option"] = "add"

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


async def get_worker_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        keyboard = build_positions_keyboard("add")
        keyboard.append(build_back_button("back_to_worker_id"))
        keyboard.append(back_to_admin_home_page_button[0])
        if update.message:
            try:
                if update.message.users_shared:
                    user_id = update.message.users_shared.users[0].user_id
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
                text=CHOOSE_POSITION_TEXT,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await update.callback_query.edit_message_text(
                text=CHOOSE_POSITION_TEXT,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        return POSITION


back_to_worker_id = add_worker


async def choose_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        worker_to_add: Chat = context.user_data["worker_to_add"]
        if not update.callback_query.data.startswith("back"):
            pos = update.callback_query.data.split("_")[1]
            context.user_data["add_worker_pos"] = pos
        else:
            pos = context.user_data["add_worker_pos"]

        keyboard = build_deposit_after_check_positions()
        keyboard.append(build_back_button("back_to_choose_add_position"))
        keyboard.append(back_to_admin_home_page_button[0])
        if pos == "deposit after check":
            await update.callback_query.edit_message_text(
                text=CHOOSE_POSITION_TEXT,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return DEPOSIT_AFTER_CHECK_POSITION
        elif pos in ["withdraw", "busdt", "deposit"]:
            keyboard = build_checker_positions_keyboard(
                op="add",
                check_what=pos,
            )
            keyboard.append(build_back_button("back_to_choose_add_position"))
            keyboard.append(back_to_admin_home_page_button[0])
            await update.callback_query.edit_message_text(
                text=CHOOSE_POSITION_TEXT,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return CHECK_POSITION
        else:
            await PaymentAgent.add_worker(
                worker_id=worker_to_add.id,
                name=worker_to_add.full_name,
                username=worker_to_add.username,
                method=pos,
            )
        keyboard = build_positions_keyboard("add")
        keyboard.append(build_back_button("back_to_worker_id"))
        keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.answer(WORKER_ADDED_SUCCESSFULLY_TEXT)
        await update.callback_query.edit_message_text(
            text=(
                WORKER_ADDED_SUCCESSFULLY_TEXT
                + "\n\n"
                + "اختر وظيفة أخرى إن إردت، للإنهاء اضغط /admin."
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


back_to_choose_add_position = get_worker_id


async def choose_deposit_after_check_position(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        worker_to_add: Chat = context.user_data["worker_to_add"]
        keyboard = build_deposit_after_check_positions()
        keyboard.append(build_back_button("back_to_choose_add_position"))
        keyboard.append(back_to_admin_home_page_button[0])
        await DepositAgent.add_worker(
            worker_id=worker_to_add.id,
            name=worker_to_add.full_name,
            username=worker_to_add.username,
            is_point=update.callback_query.data.startswith("agents"),
        )
        await update.callback_query.answer(WORKER_ADDED_SUCCESSFULLY_TEXT)
        await update.callback_query.edit_message_text(
            text=CHOOSE_POSITION_TEXT,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return DEPOSIT_AFTER_CHECK_POSITION


async def choose_check_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        method = update.callback_query.data.split("_")[1]
        worker_to_add: Chat = context.user_data["worker_to_add"]
        await Checker.add_worker(
            worker_id=worker_to_add.id,
            name=worker_to_add.full_name,
            username=worker_to_add.username,
            method=method,
            check_what=context.user_data["add_worker_pos"],
        )
        await update.callback_query.answer(WORKER_ADDED_SUCCESSFULLY_TEXT)
        keyboard = build_checker_positions_keyboard(
            check_what=context.user_data["add_worker_pos"],
            op="add",
        )
        keyboard.append(build_back_button("back_to_choose_add_position"))
        keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text=CHOOSE_POSITION_TEXT,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CHECK_POSITION


add_worker_cp_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            add_worker,
            "^add_worker$",
        )
    ],
    states={
        WORKER_ID: [
            MessageHandler(
                filters=filters.StatusUpdate.USER_SHARED,
                callback=get_worker_id,
            ),
            MessageHandler(
                filters=filters.Regex("^\d+$"),
                callback=get_worker_id,
            ),
        ],
        POSITION: [
            CallbackQueryHandler(
                choose_position,
                "^add.+((worker)|(checker))",
            ),
        ],
        CHECK_POSITION: [
            CallbackQueryHandler(
                choose_check_position,
                "^add.+checker",
            ),
        ],
        DEPOSIT_AFTER_CHECK_POSITION: [
            CallbackQueryHandler(
                choose_deposit_after_check_position,
                "^((agents)|(players))_deposit_after_check$",
            )
        ],
    },
    fallbacks=[
        back_to_admin_home_page_handler,
        admin_command,
        start_command,
        CallbackQueryHandler(back_to_worker_id, "^back_to_worker_id$"),
        CallbackQueryHandler(
            back_to_choose_add_position, "^back_to_choose_add_position$"
        ),
    ],
)
