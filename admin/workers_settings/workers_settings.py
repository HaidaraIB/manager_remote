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
    build_positions_keyboard,
    build_workers_keyboard,
    choose_position,
    create_worker_info_text,
    back_to_choose_position,
    back_to_worker_settings_handler,
    op_dict_en_to_ar,
)
from common.constants import *


async def position_to_show_remove_from(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if not update.callback_query.data.startswith("back"):
            pos = update.callback_query.data.split("_")[1]
            context.user_data[
                f"pos_to_{context.user_data['worker_settings_option']}"
            ] = pos
        else:
            pos = context.user_data[
                f"pos_to_{context.user_data['worker_settings_option']}"
            ]
        if pos == "deposit after check":
            workers = DepositAgent.get_workers()
            ans_text = "ليس لديك موظفي تنفيذ إيداعات بعد❗️"

        elif pos in ["withdraw", "buy"]:
            workers = Checker.get_workers(check_what=pos)
            ans_text = f"ليس لديك موظفي تحقق {op_dict_en_to_ar[pos]} بعد❗️"

        else:
            workers = PaymentAgent.get_workers(method=pos)
            ans_text = f"ليس لديك وكلاء {pos} بعد❗️"

        if not workers:
            await update.callback_query.answer(
                text=ans_text,
                show_alert=True,
            )
            return

        keyboard = build_workers_keyboard(
            workers,
            context.user_data["worker_settings_option"],
        )

        await update.callback_query.edit_message_text(
            text="اختر الموظف.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CHOOSE_WORKER


async def choose_worker_to_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        w_id = int(update.callback_query.data.split(" ")[1])
        t_worker = await context.bot.get_chat(chat_id=w_id)
        pos = context.user_data[f"pos_to_{context.user_data['worker_settings_option']}"]
        if pos == "deposit after check":
            worker = DepositAgent.get_workers(worker_id=w_id, deposit=True)
            workers = DepositAgent.get_workers()

        elif pos in ["withdraw", "buy"]:
            worker = Checker.get_workers(worker_id=w_id, check_what=pos)
            workers = Checker.get_workers(check_what=pos)

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
        worker_to_remove_id = int(update.callback_query.data.split(" ")[1])
        pos = context.user_data[f"pos_to_{context.user_data['worker_settings_option']}"]

        if pos == "deposit after check":
            await DepositAgent.remove_worker(worker_id=worker_to_remove_id)
            workers = DepositAgent.get_workers()

        elif pos in ["deposit", "withdraw", "buy"]:
            await Checker.remove_worker(worker_id=worker_to_remove_id, check_what=pos)
            workers = Checker.get_workers(check_what=pos)

        else:
            await PaymentAgent.remove_worker(worker_id=worker_to_remove_id, method=pos)
            workers = PaymentAgent.get_workers(method=pos)

        await update.callback_query.answer(
            text="تمت إزالة الموظف بنجاح✅",
            show_alert=True,
        )

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
            choose_position,
            "^remove worker$",
        ),
    ],
    states={
        CHOOSE_POSITION: [
            CallbackQueryHandler(
                position_to_show_remove_from,
                "^remove.+((worker)|(checker))",
            )
        ],
        CHOOSE_WORKER: [
            CallbackQueryHandler(
                choose_worker_to_remove,
                "^remove \d+$",
            ),
        ],
    },
    fallbacks=[
        back_to_admin_home_page_handler,
        admin_command,
        start_command,
        back_to_worker_settings_handler,
        CallbackQueryHandler(
            back_to_choose_position,
            "^back_to_remove$",
        ),
    ],
)


show_worker_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            choose_position,
            "^show worker$",
        ),
    ],
    states={
        CHOOSE_POSITION: [
            CallbackQueryHandler(
                position_to_show_remove_from,
                "^show.+((worker)|(checker))",
            )
        ],
        CHOOSE_WORKER: [
            CallbackQueryHandler(
                choose_worker_to_show,
                "^show \d+$",
            )
        ],
    },
    fallbacks=[
        back_to_admin_home_page_handler,
        admin_command,
        start_command,
        back_to_worker_settings_handler,
        CallbackQueryHandler(
            back_to_choose_position,
            "^back_to_show$",
        ),
    ],
)
