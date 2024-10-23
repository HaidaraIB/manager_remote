from telegram import Chat, Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
from common.back_to_home_page import (
    back_to_admin_home_page_handler,
    back_to_admin_home_page_button,
)
from common.common import build_back_button
from start import admin_command, start_command
from models import PaymentAgent, DepositAgent, Checker
from custom_filters import Admin
from admin.workers_settings.common import (
    CHOOSE_POSITION,
    CHOOSE_WORKER,
    CHECK_POSITION_SHOW_REMOVE,
    DEPOSIT_AFTER_CHECK_POSITION_SHOW_REMOVE,
    build_workers_keyboard,
    choose_option,
    create_worker_info_text,
    back_to_choose_option_handler,
    back_to_choose_position_handler,
)
from admin.workers_settings.workers_settings import (
    position_to_show_remove_from,
    choose_check_position_show_remove,
    choose_deposit_after_check_position_show_remove,
    back_to_choose_position_to_show_remove,
)


async def choose_worker_to_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        option = context.user_data["worker_settings_option"]
        w_id = int(update.callback_query.data.split("_")[1])
        t_worker = await context.bot.get_chat(chat_id=w_id)
        pos: str = context.user_data[f"pos_to_{option}"]
        if pos == "deposit after check":
            is_point = context.user_data[f"is_point_deposit_agent_to_{option}"]
            worker = DepositAgent.get_workers(worker_id=w_id, is_point=is_point)
            workers = DepositAgent.get_workers(is_point=is_point)
            back_data = "back_to_choose_position_to_show_remove"

        elif pos in ["withdraw", "busdt", "deposit"]:
            method = context.user_data[f"method_to_{option}"]
            worker = Checker.get_workers(worker_id=w_id, check_what=pos, method=method)
            workers = Checker.get_workers(check_what=pos, method=method)
            back_data = "back_to_choose_position_to_show_remove"

        else:
            worker = PaymentAgent.get_workers(worker_id=w_id, method=pos)
            workers = PaymentAgent.get_workers(method=pos)
            back_data = "back_to_choose_position"

        text = create_worker_info_text(t_worker, worker, pos) + "يمكنك عرض موظف آخر."
        keyboard = build_workers_keyboard(workers, "show")
        keyboard.append(build_back_button(back_data))
        keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
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
        DEPOSIT_AFTER_CHECK_POSITION_SHOW_REMOVE: [
            CallbackQueryHandler(
                choose_deposit_after_check_position_show_remove,
                "^show_((agents)|(players))_deposit_after_check$",
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
        back_to_choose_position_handler,
        CallbackQueryHandler(
            back_to_choose_position_to_show_remove,
            "^back_to_choose_position_to_show_remove$",
        ),
    ],
)
