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
    build_checker_positions_keyboard,
    back_to_choose_option_handler,
    back_to_choose_position_handler,
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


async def choose_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        worker_to_add: Chat = context.user_data["worker_to_add"]
        if not update.callback_query.data.startswith("back"):
            pos = update.callback_query.data.split("_")[1]
            context.user_data["add_worker_pos"] = pos
        else:
            pos = context.user_data["add_worker_pos"]

        if pos == "deposit after check":
            keyboard = [
                [
                    InlineKeyboardButton(
                        text="لاعبين",
                        callback_data="players_deposit_after_check",
                    ),
                    InlineKeyboardButton(
                        text="وكلاء",
                        callback_data="agents_deposit_after_check",
                    ),
                ],
            ]
            keyboard.append(build_back_button("back_to_choose_position"))
            keyboard.append(back_to_admin_home_page_button[0])
            await update.callback_query.edit_message_text(
                text="اختر الوظيفة:\n\nللإنهاء اضغط /admin",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return DEPOSIT_AFTER_CHECK_POSITION
        elif pos in ["withdraw", "busdt", "deposit"]:
            keyboard = build_checker_positions_keyboard(
                op="add",
                check_what=pos,
            )
            keyboard.append(build_back_button("back_to_choose_position"))
            keyboard.append(back_to_admin_home_page_button[0])
            await update.callback_query.edit_message_text(
                text="اختر الوظيفة:\n\nللإنهاء اضغط /admin",
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
        await update.callback_query.answer("تمت إضافة الموظف بنجاح✅")
        await update.callback_query.edit_message_text(
            text="تمت إضافة الموظف بنجاح✅\n\n\nاختر وظيفة أخرى إن إردت، للإنهاء اضغط /admin.",
            reply_markup=build_positions_keyboard(op="add"),
        )


back_to_worker_id = choose_position


async def choose_deposit_after_check_position(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        worker_to_add: Chat = context.user_data["worker_to_add"]
        await DepositAgent.add_worker(
            worker_id=worker_to_add.id,
            name=worker_to_add.full_name,
            username=worker_to_add.username,
            is_point=update.callback_query.data.startswith("agents"),
        )
        await update.callback_query.answer("تمت إضافة الموظف بنجاح✅")
        keyboard = [
            [
                InlineKeyboardButton(
                    text="لاعبين",
                    callback_data="players_deposit_after_check",
                ),
                InlineKeyboardButton(
                    text="وكلاء",
                    callback_data="agents_deposit_after_check",
                ),
            ],
        ]
        keyboard.append(build_back_button("back_to_choose_position"))
        keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر الوظيفة:\n\nللإنهاء اضغط /admin",
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
        await update.callback_query.answer("تمت إضافة الموظف بنجاح✅")
        keyboard = build_checker_positions_keyboard(
            check_what=context.user_data["add_worker_pos"],
            op="add",
        )
        keyboard.append(build_back_button("back_to_choose_position"))
        keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر الوظيفة:\n\nللإنهاء اضغط /admin",
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
                callback=worker_id,
            ),
            MessageHandler(
                filters=filters.Regex("^\d+$"),
                callback=worker_id,
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
        back_to_choose_position_handler,
        back_to_choose_option_handler,
        CallbackQueryHandler(back_to_worker_id, "^back_to_worker_id$"),
    ],
)
