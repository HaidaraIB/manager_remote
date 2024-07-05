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

from common.common import op_dict_en_to_ar, build_back_button

from common.back_to_home_page import (
    back_to_admin_home_page_handler,
    back_to_admin_home_page_button,
)

from start import admin_command

from DB import DB
from custom_filters.Admin import Admin
from admin.workers_settings.common import build_payment_positions_keyboard
from constants import *

(CHOOSE_PAYMENT_POSITION, CHOOSE_WORKER_BALANCE, GET_PRE_BALANCE_AMOUNT) = range()


async def worker_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        worker_balance_keyboard = build_payment_positions_keyboard("balance")
        worker_balance_keyboard.append(build_back_button("back_to_worker_balance"))
        worker_balance_keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اعدادات رصيد الموظفين، اختر الوظيفة",
            reply_markup=InlineKeyboardMarkup(worker_balance_keyboard),
        )
        return CHOOSE_PAYMENT_POSITION


async def choose_payment_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        context.user_data["balance_pos"] = update.callback_query.data.split(" ")[1]


async def choose_worker_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        data = update.callback_query.data
        back_buttons = [
            build_back_button("back_to_choose_worker_balance"),
            back_to_admin_home_page_button[0],
        ]
        if data == "send_pre_balance":
            await update.callback_query.edit_message_text(
                text="أرسل مقدار الدفعة المسبقة",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return GET_PRE_BALANCE_AMOUNT


async def get_pre_balance_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if not update.callback_query:
            context.user_data["pre_balance_amount"] = float(update.message.text)
        await update.callback_query.edit_message_text()
