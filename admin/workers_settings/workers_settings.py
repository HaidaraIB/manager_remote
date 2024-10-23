from telegram import Chat, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models import PaymentAgent, DepositAgent, Checker
from custom_filters import Admin
from common.common import build_back_button, order_dict_en_to_ar
from common.back_to_home_page import back_to_admin_home_page_button
from admin.workers_settings.common import (
    CHOOSE_WORKER,
    CHECK_POSITION_SHOW_REMOVE,
    DEPOSIT_AFTER_CHECK_POSITION_SHOW_REMOVE,
    build_workers_keyboard,
    build_checker_positions_keyboard,
)


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
            keyboard.append(build_back_button("back_to_choose_position"))
            keyboard.append(back_to_admin_home_page_button[0])
            await update.callback_query.edit_message_text(
                text="اختر الوظيفة:",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return CHECK_POSITION_SHOW_REMOVE

        elif pos == "deposit after check":
            keyboard = [
                [
                    InlineKeyboardButton(
                        text="لاعبين",
                        callback_data=f"{option}_players_deposit_after_check",
                    ),
                    InlineKeyboardButton(
                        text="وكلاء",
                        callback_data=f"{option}_agents_deposit_after_check",
                    ),
                ],
            ]
            keyboard.append(build_back_button("back_to_choose_position"))
            keyboard.append(back_to_admin_home_page_button[0])
            await update.callback_query.edit_message_text(
                text="اختر الوظيفة:",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return DEPOSIT_AFTER_CHECK_POSITION_SHOW_REMOVE
        else:
            workers = PaymentAgent.get_workers(method=pos)
            ans_text = f"ليس لديك وكلاء {pos} بعد ❗️"

        if not workers:
            await update.callback_query.answer(
                text=ans_text,
                show_alert=True,
            )
            return

        keyboard = build_workers_keyboard(workers, option)
        keyboard.append(build_back_button(f"back_to_choose_position"))
        keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر الموظف.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CHOOSE_WORKER


async def choose_deposit_after_check_position_show_remove(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        option = context.user_data["worker_settings_option"]
        is_point = update.callback_query.data.startswith("agents")
        context.user_data[f"is_point_deposit_agent_to_{option}"] = is_point
        workers = DepositAgent.get_workers(is_point=is_point)

        if not workers:
            await update.callback_query.answer(
                text="ليس لديك موظفي تنفيذ إيداعات بعد ❗️",
                show_alert=True,
            )
            return
        keyboard = build_workers_keyboard(workers, option)
        keyboard.append(
            build_back_button(
                f"back_to_choose_position_to_show_remove"
            )
        )
        keyboard.append(back_to_admin_home_page_button[0])
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
        if not update.callback_query.data.startswith("back"):
            method = update.callback_query.data.split("_")[1]
            context.user_data[f"method_to_{option}"] = method
        else:
            method = context.user_data[f"method_to_{option}"]

        workers = Checker.get_workers(check_what=pos, method=method)

        if not workers:
            await update.callback_query.answer(
                text=f"ليس لديك موظفي تحقق {order_dict_en_to_ar[pos]} {method} بعد ❗️",
                show_alert=True,
            )
            return
        keyboard = build_workers_keyboard(workers, option)
        keyboard.append(build_back_button(f"back_to_choose_position_to_show_remove"))
        keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر الموظف.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CHOOSE_WORKER


back_to_choose_position_to_show_remove = position_to_show_remove_from
