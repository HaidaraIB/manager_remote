from telegram import (
    Chat,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)

from common.common import (
    op_dict_en_to_ar,
)

from common.back_to_home_page import (
    back_to_admin_home_page_handler,
)

from start import admin_command

from DB import DB
from custom_filters.Admin import Admin
from admin.workers_settings.common import (
    POSITION_TO_REMOVE_FROM,
    POSITION_TO_SHOW,
    build_positions_keyboard,
    build_workers_keyboard,
    choose_position,
    create_worker_info_text,
    back_to_choose_position,
    back_to_worker_settings_handler,
)
from constants import *

CHOOSE_WORKER_TO_REMOVE = CHOOSE_WORKER_TO_SHOW = 1


async def position_to_remove_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if not update.callback_query.data.startswith("back"):
            pos = update.callback_query.data.split("_")[1]
            context.user_data["pos_to_remove_from"] = pos
        else:
            pos = context.user_data["pos_to_remove_from"]
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

        keyboard = build_workers_keyboard(workers, "remove")

        await update.callback_query.edit_message_text(
            text="اختر الموظف الذي تريد إزالته.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CHOOSE_WORKER_TO_REMOVE


async def choose_worker_to_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        worker_to_remove_id = int(update.callback_query.data.split(" ")[1])
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

        keyboard = build_workers_keyboard(workers, "remove")

        await update.callback_query.edit_message_text(
            text="اختر الموظف الذي تريد إزالته.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CHOOSE_WORKER_TO_REMOVE


async def position_to_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if not update.callback_query.data.startswith("back"):
            pos = update.callback_query.data.split("_")[1]
            context.user_data["pos_to_show"] = pos
        else:
            pos = context.user_data["pos_to_show"]
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

        keyboard = build_workers_keyboard(workers, "show")

        await update.callback_query.edit_message_text(
            text="اختر الموظف الذي تريد عرضه.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CHOOSE_WORKER_TO_SHOW


async def choose_worker_to_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        w_id = int(update.callback_query.data.split(" ")[1])
        t_worker = await context.bot.get_chat(chat_id=w_id)
        pos = context.user_data["pos_to_show"]
        if pos == "deposit after check":
            worker = DB.get_worker(worker_id=w_id)
            workers = DB.get_workers()

        elif pos in ["deposit", "withdraw", "buy_usdt"]:
            worker = DB.get_worker(worker_id=w_id, check_what=pos)
            workers = DB.get_workers(check_what=pos)

        else:
            worker = DB.get_worker(worker_id=w_id, method=pos)
            workers = DB.get_workers(method=pos)

        text = create_worker_info_text(t_worker, worker, pos) + "يمكنك عرض موظف آخر."
        keyboard = build_workers_keyboard(workers, "show")
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


remove_worker_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(choose_position, "^remove worker$"),
    ],
    states={
        POSITION_TO_REMOVE_FROM: [
            CallbackQueryHandler(
                position_to_remove_from, "^remove.+((worker)|(checker))"
            )
        ],
        CHOOSE_WORKER_TO_REMOVE: [
            CallbackQueryHandler(choose_worker_to_remove, "^remove \d+$")
        ],
    },
    fallbacks=[
        back_to_admin_home_page_handler,
        admin_command,
        back_to_worker_settings_handler,
        CallbackQueryHandler(back_to_choose_position, "^back to remove$"),
    ],
)


show_worker_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(choose_position, "^show worker$"),
    ],
    states={
        POSITION_TO_SHOW: [
            CallbackQueryHandler(position_to_show, "^show.+((worker)|(checker))")
        ],
        CHOOSE_WORKER_TO_SHOW: [
            CallbackQueryHandler(choose_worker_to_show, "^show \d+$")
        ],
    },
    fallbacks=[
        back_to_admin_home_page_handler,
        admin_command,
        back_to_worker_settings_handler,
        CallbackQueryHandler(back_to_choose_position, "^back to show$"),
    ],
)
