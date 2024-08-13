from telegram import (
    Chat,
    Update,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)


from common.back_to_home_page import (
    back_to_admin_home_page_handler,
)

from start import admin_command, start_command

from models import PaymentAgent, DepositAgent, Checker
from custom_filters import Admin
from admin.workers_settings.common import (
    CHOOSE_POSITION,
    CHOOSE_WORKER,
    CHECK_POSITION_SHOW_REMOVE,
    build_positions_keyboard,
    build_workers_keyboard,
    choose_option,
    create_worker_info_text,
    build_checker_positions_keyboard,
    back_to_choose_position,
    back_to_choose_option_handler,
)
from common.common import build_back_button, op_dict_en_to_ar
from common.back_to_home_page import back_to_admin_home_page_button
from common.constants import *


async def position_to_show_remove_from(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        option = context.user_data["worker_settings_option"]
        if not update.callback_query.data.startswith("back"):
            pos = update.callback_query.data.split("_")[1]
            context.user_data[f"pos_to_{option}"] = pos
        else:
            pos = context.user_data[f"pos_to_{option}"]

        if pos in ["withdraw", "busdt", "deposit"]:
            keyboard = build_checker_positions_keyboard(
                op=option,
                check_what=pos,
            )
            keyboard.append(build_back_button(f"back_to_{option}"))
            keyboard.append(back_to_admin_home_page_button[0])
            await update.callback_query.edit_message_text(
                text="اختر الوظيفة:\n\nللإنهاء اضغط /admin",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return CHECK_POSITION_SHOW_REMOVE

        elif pos == "deposit after check":
            workers = DepositAgent.get_workers()
            ans_text = "ليس لديك موظفي تنفيذ إيداعات بعد ❗️"

        else:
            workers = PaymentAgent.get_workers(method=pos)
            ans_text = f"ليس لديك وكلاء {pos} بعد ❗️"

        if not workers:
            await update.callback_query.answer(
                text=ans_text,
                show_alert=True,
            )
            return

        keyboard = build_workers_keyboard(
            workers,
            option,
        )

        await update.callback_query.edit_message_text(
            text="اختر الموظف.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CHOOSE_WORKER


async def choose_check_position_show_remove(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        option = context.user_data["worker_settings_option"]
        pos = context.user_data[f"pos_to_{option}"]

        method = update.callback_query.data.split("_")[1]
        context.user_data[f"method_to_{option}"] = method

        workers = Checker.get_workers(check_what=pos, method=method)
        ans_text = f"ليس لديك موظفي تحقق {op_dict_en_to_ar[pos]} {method} بعد ❗️"

        if not workers:
            await update.callback_query.answer(
                text=ans_text,
                show_alert=True,
            )
            return
        keyboard = build_workers_keyboard(
            workers,
            option,
        )

        await update.callback_query.edit_message_text(
            text="اختر الموظف.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CHOOSE_WORKER


async def choose_worker_to_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        option = context.user_data["worker_settings_option"]
        w_id = int(update.callback_query.data.split("_")[1])
        t_worker = await context.bot.get_chat(chat_id=w_id)
        pos: str = context.user_data[f"pos_to_{option}"]
        if pos == "deposit after check":
            worker = DepositAgent.get_workers(worker_id=w_id, deposit=True)
            workers = DepositAgent.get_workers()

        elif pos in ["withdraw", "busdt", "deposit"]:
            method = context.user_data[f"method_to_{option}"]
            worker = Checker.get_workers(
                worker_id=w_id,
                check_what=pos,
                method=method,
            )
            workers = Checker.get_workers(
                check_what=pos,
                method=method,
            )

        else:
            worker = PaymentAgent.get_workers(worker_id=w_id, method=pos)
            workers = PaymentAgent.get_workers(method=pos)

        text = create_worker_info_text(t_worker, worker, pos) + "يمكنك عرض موظف آخر."
        keyboard = build_workers_keyboard(workers, "show")
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def choose_worker_to_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        worker_to_remove_id = int(update.callback_query.data.split("_")[1])
        option = context.user_data["worker_settings_option"]
        pos: str = context.user_data[f"pos_to_{option}"]

        if pos == "deposit after check":
            await DepositAgent.remove_worker(worker_id=worker_to_remove_id)
            workers = DepositAgent.get_workers()

        elif pos in ["withdraw", "busdt", "deposit"]:
            method = context.user_data[f"method_to_{option}"]
            await Checker.remove_worker(
                worker_id=worker_to_remove_id,
                check_what=pos,
                method=method,
            )
            workers = Checker.get_workers(
                check_what=pos,
                method=method,
            )

        else:
            await PaymentAgent.remove_worker(worker_id=worker_to_remove_id, method=pos)
            workers = PaymentAgent.get_workers(method=pos)

        await update.callback_query.answer(text="تمت إزالة الموظف بنجاح✅")

        if not workers:
            await update.callback_query.edit_message_text(
                text="اختر الوظيفة:",
                reply_markup=build_positions_keyboard(op="remove"),
            )

            return CHOOSE_POSITION

        keyboard = build_workers_keyboard(workers, "remove")

        await update.callback_query.edit_message_text(
            text="اختر الموظف.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CHOOSE_WORKER


remove_worker_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            choose_option,
            "^remove_worker$",
        ),
    ],
    states={
        CHOOSE_POSITION: [
            CallbackQueryHandler(
                position_to_show_remove_from,
                "^remove.+((worker)|(checker))",
            )
        ],
        CHECK_POSITION_SHOW_REMOVE: [
            CallbackQueryHandler(
                choose_check_position_show_remove,
                "^remove.+checker",
            )
        ],
        CHOOSE_WORKER: [
            CallbackQueryHandler(
                choose_worker_to_remove,
                "^remove_\d+$",
            ),
        ],
    },
    fallbacks=[
        back_to_admin_home_page_handler,
        admin_command,
        start_command,
        back_to_choose_option_handler,
        CallbackQueryHandler(
            back_to_choose_position,
            "^back_to_remove$",
        ),
    ],
)


show_worker_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            choose_option,
            "^show_worker$",
        ),
    ],
    states={
        CHOOSE_POSITION: [
            CallbackQueryHandler(
                position_to_show_remove_from,
                "^show.+((worker)|(checker))",
            )
        ],
        CHECK_POSITION_SHOW_REMOVE: [
            CallbackQueryHandler(
                choose_check_position_show_remove,
                "^show.+checker",
            )
        ],
        CHOOSE_WORKER: [
            CallbackQueryHandler(
                choose_worker_to_show,
                "^show_\d+$",
            )
        ],
    },
    fallbacks=[
        back_to_admin_home_page_handler,
        admin_command,
        start_command,
        back_to_choose_option_handler,
        CallbackQueryHandler(
            back_to_choose_position,
            "^back_to_show$",
        ),
    ],
)
