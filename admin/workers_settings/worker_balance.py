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
    MessageHandler,
    filters,
)

from common.common import (
    build_back_button,
    build_admin_keyboard,
)

from common.back_to_home_page import (
    back_to_admin_home_page_handler,
    back_to_admin_home_page_button,
)

from start import admin_command

from DB import DB
from custom_filters.Admin import Admin
from admin.workers_settings.common import (
    CHOOSE_POSITION,
    CHOOSE_WORKER,
    build_workers_keyboard,
    choose_position,
    create_worker_info_text,
    back_to_choose_position,
    back_to_worker_settings_handler,
)
from constants import *

(
    CHOOSE_WORKER_BALANCE,
    GET_PRE_BALANCE_AMOUNT,
) = range(2, 4)


async def position_for_worker_balance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if not update.callback_query.data.startswith("back"):
            pos = update.callback_query.data.split("_")[1]
            context.user_data["balance_pos"] = pos
        else:
            pos = context.user_data["balance_pos"]
        workers = DB.get_workers(method=pos)
        if not workers:
            await update.callback_query.answer(f"لا يوجد موظفين سحب {pos} بعد!")
            return
        await update.callback_query.edit_message_text(
            text="اختر الموظف",
            reply_markup=InlineKeyboardMarkup(
                build_workers_keyboard(
                    workers=workers,
                    t="balance",
                )
            ),
        )
        return CHOOSE_WORKER


async def worker_for_worker_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if not update.callback_query.data.startswith("back"):
            w_id = int(update.callback_query.data.split(" ")[1])
            context.user_data["worker_balance_id"] = w_id

        t_worker = await context.bot.get_chat(
            chat_id=context.user_data["worker_balance_id"]
        )
        pos = context.user_data["balance_pos"]

        worker = DB.get_worker(worker_id=t_worker.id, method=pos)
        text = create_worker_info_text(t_worker, worker, pos)
        keyboard = [
            [
                InlineKeyboardButton(
                    text="إرسال دفعة مسبقة",
                    callback_data="send_pre_balance",
                )
            ],
            build_back_button("back_to_worker_for_worker_balance"),
            back_to_admin_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CHOOSE_WORKER_BALANCE


back_to_worker_for_worker_balance = position_for_worker_balance


async def choose_worker_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        data = update.callback_query.data
        back_buttons = [
            build_back_button("back_to_choose_worker_balance"),
            back_to_admin_home_page_button[0],
        ]
        if data == "send_pre_balance":
            await update.callback_query.answer(
                text="أرسل الدفعة المسبقة",
                show_alert=True,
            )
            await update.callback_query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return GET_PRE_BALANCE_AMOUNT


back_to_choose_worker_balance = worker_for_worker_balance


async def get_pre_balance_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        await DB.add_pre_balance(
            amount=float(update.message.text),
            worker_id=context.user_data["worker_balance_id"],
            method=context.user_data["balance_pos"],
        )
        await update.message.reply_text(
            text="تمت إضافة الدفعة المسبقة بنجاح ✅",
            reply_markup=build_admin_keyboard(),
        )
        return ConversationHandler.END


worker_balance_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(choose_position, "^balance worker$"),
    ],
    states={
        CHOOSE_POSITION: [
            CallbackQueryHandler(
                position_for_worker_balance,
                "^balance.+worker$",
            )
        ],
        CHOOSE_WORKER: [
            CallbackQueryHandler(
                worker_for_worker_balance,
                "^balance \d+$",
            )
        ],
        CHOOSE_WORKER_BALANCE: [
            CallbackQueryHandler(
                choose_worker_balance,
                "^send_pre_balance$",
            )
        ],
        GET_PRE_BALANCE_AMOUNT: [
            MessageHandler(
                filters=filters.Regex("^\d+.?\d*$"),
                callback=get_pre_balance_amount,
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_worker_for_worker_balance,
            "^back_to_worker_for_worker_balance$",
        ),
        CallbackQueryHandler(
            back_to_choose_position,
            "^back_to_balance$",
        ),
        CallbackQueryHandler(
            back_to_choose_worker_balance,
            "^back_to_choose_worker_balance$",
        ),
        back_to_worker_settings_handler,
        back_to_admin_home_page_handler,
        admin_command,
    ],
)
