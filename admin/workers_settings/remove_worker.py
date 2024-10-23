from telegram import Chat, Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
from common.common import build_back_button
from common.back_to_home_page import (
    back_to_admin_home_page_handler,
    back_to_admin_home_page_button,
)
from start import admin_command, start_command
from models import PaymentAgent, DepositAgent, Checker
from custom_filters import Admin
from admin.workers_settings.common import (
    CHOOSE_POSITION,
    CHOOSE_WORKER,
    CHECK_POSITION_SHOW_REMOVE,
    DEPOSIT_AFTER_CHECK_POSITION_SHOW_REMOVE,
    build_positions_keyboard,
    build_workers_keyboard,
    choose_option,
    back_to_choose_option_handler,
    back_to_choose_position_handler,
)
from admin.workers_settings.workers_settings import (
    position_to_show_remove_from,
    choose_check_position_show_remove,
    choose_deposit_after_check_position_show_remove,
    back_to_choose_position_to_show_remove,
)


async def choose_worker_to_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        worker_to_remove_id = int(update.callback_query.data.split("_")[1])
        option = context.user_data["worker_settings_option"]
        pos: str = context.user_data[f"pos_to_{option}"]

        if pos == "deposit after check":
            is_point = context.user_data[f"is_point_deposit_agent_to_{option}"]
            await DepositAgent.remove_worker(
                worker_id=worker_to_remove_id, is_point=is_point
            )
            workers = DepositAgent.get_workers(is_point=is_point)
            back_data = "back_to_choose_position_to_show_remove"

        elif pos in ["withdraw", "busdt", "deposit"]:
            method = context.user_data[f"method_to_{option}"]
            await Checker.remove_worker(
                worker_id=worker_to_remove_id, check_what=pos, method=method
            )
            workers = Checker.get_workers(check_what=pos, method=method)
            back_data = "back_to_choose_position_to_show_remove"

        else:
            await PaymentAgent.remove_worker(worker_id=worker_to_remove_id, method=pos)
            workers = PaymentAgent.get_workers(method=pos)
            back_data = "back_to_choose_position"

        keyboard = build_positions_keyboard("remove")
        keyboard.append(build_back_button("back_to_choose_option"))
        keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.answer(text="تمت إزالة الموظف بنجاح ✅")
        if not workers:
            await update.callback_query.edit_message_text(
                text="اختر الوظيفة:",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return CHOOSE_POSITION

        keyboard = build_workers_keyboard(workers, "remove")
        keyboard.append(build_back_button(back_data))
        keyboard.append(back_to_admin_home_page_button[0])
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
        DEPOSIT_AFTER_CHECK_POSITION_SHOW_REMOVE: [
            CallbackQueryHandler(
                choose_deposit_after_check_position_show_remove,
                "^remove_((agents)|(players))_deposit_after_check$",
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
        back_to_choose_position_handler,
        CallbackQueryHandler(
            back_to_choose_position_to_show_remove,
            "^back_to_choose_position_to_show_remove$",
        ),
    ],
)
