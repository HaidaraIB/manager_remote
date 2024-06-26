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

from common.common import (
    op_dict_en_to_ar,
)

from common.back_to_home_page import (
    back_to_admin_home_page_handler,
    back_to_admin_home_page_button
)

from start import start_command

from DB import DB
from custom_filters.Admin import Admin

(
    WORKER_ID,
    POSITION,
    POSITION_TO_REMOVE_FROM,
    CHOOSE_WORKER_TO_REMOVE,
    POSITION_TO_SHOW,
    CHOOSE_WORKER_TO_SHOW,
) = range(6)


def build_workers_keyboard(
    workers: list, show: bool = False
) -> list[list[InlineKeyboardButton]]:
    if len(workers) == 1:
        keyboard = [
            [
                InlineKeyboardButton(
                    text=workers[0]["name"],
                    callback_data=(
                        "s" + str(workers[0]["id"]) if show else str(workers[0]["id"])
                    ),
                )
            ]
        ]
    elif len(workers) % 2 == 0:
        keyboard = [
            [
                InlineKeyboardButton(
                    text=workers[i]["name"],
                    callback_data=(
                        "s" + str(workers[i]["id"]) if show else str(workers[i]["id"])
                    ),
                ),
                InlineKeyboardButton(
                    text=workers[i + 1]["name"],
                    callback_data=(
                        "s" + str(workers[i + 1]["id"])
                        if show
                        else str(workers[i + 1]["id"])
                    ),
                ),
            ]
            for i in range(0, len(workers), 2)
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    text=workers[i]["name"],
                    callback_data=(
                        "s" + str(workers[i]["id"]) if show else str(workers[i]["id"])
                    ),
                ),
                InlineKeyboardButton(
                    text=workers[i + 1]["name"],
                    callback_data=(
                        "s" + str(workers[i + 1]["id"])
                        if show
                        else str(workers[i + 1]["id"])
                    ),
                ),
            ]
            for i in range(0, len(workers) - 1, 2)
        ]
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=workers[-1]["name"],
                    callback_data=(
                        "s" + str(workers[-1]["id"]) if show else str(workers[-1]["id"])
                    ),
                )
            ],
        )
    keyboard.append(
        [
            InlineKeyboardButton(
                text="الرجوع🔙",
                callback_data=(
                    "back to pos to show" if show else "back to pos to remove from"
                ),
            )
        ]
    )
    keyboard.append(back_to_admin_home_page_button[0])
    return keyboard


def build_positions_keyboard(op: str = "add"):
    add_worker_keyboard = [
        [
            InlineKeyboardButton(
                text="تنفيذ إيداع",
                callback_data=f"{op} deposit after check worker",
            )
        ],
        [
            InlineKeyboardButton(
                text="تحقق إيداع", callback_data=f"{op} deposit checker"
            ),
            InlineKeyboardButton(
                text="تحقق سحب", callback_data=f"{op} withdraw checker"
            ),
            InlineKeyboardButton(
                text="تحقق شراء USDT", callback_data=f"{op} buy_usdt checker"
            ),
        ],
        [
            InlineKeyboardButton(text="دفع USDT", callback_data=f"{op} USDT worker"),
            InlineKeyboardButton(
                text="دفع بركة🇧🇭", callback_data=f"{op} بركة🇧🇭 worker"
            ),
            InlineKeyboardButton(
                text="دفع Syriatel Cash🇸🇾",
                callback_data=f"{op} Syriatel Cash🇸🇾 worker",
            ),
            InlineKeyboardButton(
                text="دفع MTN Cash🇸🇾", callback_data=f"{op} MTN Cash🇸🇾 worker"
            ),
            InlineKeyboardButton(
                text="دفع بيمو🇸🇦🇫🇷", callback_data=f"{op} بيمو🇸🇦🇫🇷 worker"
            ),
        ],
        (
            [InlineKeyboardButton(text="الرجوع🔙", callback_data="back to worker id")]
            if op == "add"
            else []
        ),
        back_to_admin_home_page_button[0] if op != 'add' else []
    ]
    return InlineKeyboardMarkup(add_worker_keyboard)


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
                text="لم يتم العثور على الحساب❗️، تأكد من أن الموظف قد بدأ محادثة مع البوت، يمكنك إلغاء العملية بالضغط على /admin.",
            )
            return
        context.user_data["worker_to_add"] = worker_to_add

        await update.message.reply_text(
            text="تم العثور على الحساب✅",
            reply_markup=ReplyKeyboardRemove(),
        )
        await update.message.reply_text(
            text="اختر الوظيفة:\n\nللإنهاء اضغط /start",
            reply_markup=build_positions_keyboard(),
        )
        return POSITION


async def position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        worker_to_add: Chat = context.user_data["worker_to_add"]
        pos = " ".join(update.callback_query.data.split(" ")[1:-1])
        if pos == "deposit after check":
            await DB.add_worker(
                worker_id=worker_to_add.id,
                name=worker_to_add.full_name,
                username=worker_to_add.username,
            )
        elif pos in ["deposit", "withdraw", "buy_usdt"]:
            await DB.add_worker(
                worker_id=worker_to_add.id,
                name=worker_to_add.full_name,
                username=worker_to_add.username,
                check_what=pos,
            )
        else:
            await DB.add_worker(
                worker_id=worker_to_add.id,
                name=worker_to_add.full_name,
                username=worker_to_add.username,
                method=pos,
            )
        await update.callback_query.answer("تمت إضافة الموظف بنجاح✅")
        await update.callback_query.edit_message_text(
            text="تمت إضافة الموظف بنجاح✅\n\n\nاختر وظيفة أخرى إن إردت، للإنهاء اضغط /start.",
            reply_markup=build_positions_keyboard(),
        )
        return


async def remove_worker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        await update.callback_query.edit_message_text(
            text="اختر الوظيفة:",
            reply_markup=build_positions_keyboard(op="remove"),
        )
        return POSITION_TO_REMOVE_FROM


async def position_to_remove_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        pos = " ".join(update.callback_query.data.split(" ")[1:-1])
        context.user_data["pos_to_remove_from"] = pos
        if pos == "deposit after check":
            workers = DB.get_workers()
            ans_text = "ليس لديك موظفي تنفيذ إيداعات بعد❗️"

        elif pos in ["deposit", "withdraw", "buy_usdt"]:
            workers = DB.get_workers(check_what=pos)
            ans_text = f"ليس لديك موظفي تحقق {op_dict_en_to_ar[pos]} بعد❗️"

        else:
            workers = DB.get_workers(method=pos)
            ans_text = f"ليس لديك وكلاء {pos} بعد❗️"

        if not workers:
            await update.callback_query.answer(ans_text)
            return

        keyboard = build_workers_keyboard(workers)

        await update.callback_query.edit_message_text(
            text="اختر الموظف الذي تريد إزالته.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CHOOSE_WORKER_TO_REMOVE


async def choose_worker_to_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        worker_to_remove_id = int(update.callback_query.data)
        pos = context.user_data["pos_to_remove_from"]

        if pos == "deposit after check":
            await DB.remove_worker(worker_id=worker_to_remove_id)
            workers = DB.get_workers()

        elif pos in ["deposit", "withdraw", "buy_usdt"]:
            await DB.remove_worker(worker_id=worker_to_remove_id, check_what=pos)
            workers = DB.get_workers(check_what=pos)

        else:
            await DB.remove_worker(worker_id=worker_to_remove_id, method=pos)
            workers = DB.get_workers(method=pos)

        await update.callback_query.answer("تمت إزالة الموظف بنجاح✅")

        if not workers:
            await update.callback_query.edit_message_text(
                text="اختر الوظيفة:",
                reply_markup=build_positions_keyboard(op="remove"),
            )

            return POSITION_TO_REMOVE_FROM

        keyboard = build_workers_keyboard(workers)

        await update.callback_query.edit_message_text(
            text="اختر الموظف الذي تريد إزالته.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CHOOSE_WORKER_TO_REMOVE


async def show_workers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        await update.callback_query.edit_message_text(
            text="اختر الوظيفة:",
            reply_markup=build_positions_keyboard(op="show"),
        )
        return POSITION_TO_SHOW


async def position_to_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        pos = " ".join(update.callback_query.data.split(" ")[1:-1])
        context.user_data["pos_to_show"] = pos
        if pos == "deposit after check":
            workers = DB.get_workers()
            ans_text = "ليس لديك موظفي تنفيذ إيداعات بعد❗️"

        elif pos in ["deposit", "withdraw", "buy_usdt"]:
            workers = DB.get_workers(check_what=pos)
            ans_text = f"ليس لديك موظفي تحقق {op_dict_en_to_ar[pos]} بعد❗️"

        else:
            workers = DB.get_workers(method=pos)
            ans_text = f"ليس لديك وكلاء {pos} بعد❗️"

        if not workers:
            await update.callback_query.answer(ans_text)
            return

        keyboard = build_workers_keyboard(workers, show=True)

        await update.callback_query.edit_message_text(
            text="اختر الموظف الذي تريد عرضه.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CHOOSE_WORKER_TO_SHOW


async def choose_worker_to_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        w_id = int(update.callback_query.data[1:])
        pos = context.user_data["pos_to_show"]
        if pos == "deposit after check":
            worker = DB.get_worker(worker_id=w_id)
            workers = DB.get_workers()
            text = (
                f"آيدي الموظف: <code>{worker['id']}</code>\n"
                f"اسمه: <b>{worker['name']}</b>\n"
                f"اسم المستخدم: {'@' + worker['username'] if worker['username'] else 'لا يوجد'}\n"
                f"الإيداعات حتى الآن: {worker['approved_deposits']}\n"
                f"عددها: {worker['approved_deposits_num']}\n"
                f"الإيداعات هذا الاسبوع: {worker['approved_deposits_week']}\n"
                f"رصيد المكافآت: {worker['weekly_rewards_balance']}\n"
            )

        elif pos in ["deposit", "withdraw", "buy_usdt"]:
            worker = DB.get_worker(worker_id=w_id, check_what=pos)
            workers = DB.get_workers(check_what=pos)
            text = (
                f"آيدي الموظف: <code>{worker['id']}</code>\n"
                f"اسمه: <b>{worker['name']}</b>\n"
                f"اسم المستخدم: {'@' + worker['username'] if worker['username'] else 'لا يوجد'}\n"
                f"نوع التحقق: {worker['check_what']}\n"
            )

        else:
            worker = DB.get_worker(worker_id=w_id, method=pos)
            workers = DB.get_workers(method=pos)
            text = (
                f"آيدي الموظف: <code>{worker['id']}</code>\n"
                f"اسمه: <b>{worker['name']}</b>\n"
                f"اسم المستخدم: {'@' + worker['username'] if worker['username'] else 'لا يوجد'}\n"
                f"السحوبات حتى الآن: {worker['approved_withdraws']}\n"
                f"عددها: {worker['approved_withdraws_num']}\n"
                f"السحوبات هذا الاسبوع: {worker['approved_withdraws_day']}\n"
                f"رصيد المكافآت: {worker['daily_rewards_balance']}\n"
            )

        text += "يمكنك عرض موظف آخر."
        keyboard = build_workers_keyboard(workers, show=True)
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


back_to_worker_id = add_worker_cp

back_to_pos_to_remove_from = remove_worker

back_to_pos_to_show = show_workers

worker_settings_handler = CallbackQueryHandler(worker_settings, "^worker settings$")

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
        POSITION: [CallbackQueryHandler(position, "^add.+((worker)|(checker))")],
    },
    fallbacks=[
        back_to_admin_home_page_handler,
        start_command,
        CallbackQueryHandler(back_to_worker_id, "^back to worker id$"),
    ],
)

remove_worker_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(remove_worker, "^remove worker$"),
    ],
    states={
        POSITION_TO_REMOVE_FROM: [
            CallbackQueryHandler(
                position_to_remove_from, "^remove.+((worker)|(checker))"
            )
        ],
        CHOOSE_WORKER_TO_REMOVE: [
            CallbackQueryHandler(choose_worker_to_remove, "^\d+$")
        ],
    },
    fallbacks=[
        back_to_admin_home_page_handler,
        start_command,
        CallbackQueryHandler(
            back_to_pos_to_remove_from, "^back to pos to remove from$"
        ),
    ],
)


show_worker_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(show_workers, "^show worker$"),
    ],
    states={
        POSITION_TO_SHOW: [
            CallbackQueryHandler(position_to_show, "^show.+((worker)|(checker))")
        ],
        CHOOSE_WORKER_TO_SHOW: [CallbackQueryHandler(choose_worker_to_show, "^s\d+$")],
    },
    fallbacks=[
        back_to_admin_home_page_handler,
        start_command,
        CallbackQueryHandler(back_to_pos_to_show, "^back to pos to show$"),
    ],
)
