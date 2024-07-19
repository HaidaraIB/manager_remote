from telegram import (
    Chat,
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from common.common import build_admin_keyboard, build_back_button

from common.back_to_home_page import (
    back_to_admin_home_page_handler,
    back_to_admin_home_page_button,
    back_to_admin_home_page_button,
)

from start import admin_command, start_command

from custom_filters import Admin

NEW_PERCENTAGE = 0


async def update_percentages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        keyboard = [
            [
                InlineKeyboardButton(
                    text="تعديل نسبة مكافأة الموظفين الأسبوعية🧑🏻‍💻",
                    callback_data="update workers_reward_percentage",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="تعديل نسبة مكافأة الموظفين اليومية🧑🏻‍💻",
                    callback_data="update workers_reward_withdraw_percentage",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="تعديل نسبة مكافأة الإيداع🏆",
                    callback_data="update deposit_gift_percentage",
                )
            ],
            back_to_admin_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="اختر النسبة التي تريد تعديلها:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ConversationHandler.END



reward_percentages_dict = {
    "workers_reward_withdraw_percentage": "مكافأة الموظفين اليومية الجديدة",
    "workers_reward_percentage": "مكافأة الموظفين الأسبوعية الجديدة",
    "deposit_gift_percentage": "مكافأة الإيداع الجديدة",
    "workers_reward_withdraw_percentage": "مكافأة الموظفين اليومية الجديدة",
    "workers_reward_percentage": "مكافأة الموظفين الأسبوعية الجديدة",
    "deposit_gift_percentage": "مكافأة الإيداع الجديدة",
}



async def update_percentage(update: Update, context: ContextTypes.DEFAULT_TYPE):
async def update_percentage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        target_percentage = update.callback_query.data.replace("update ", "")
        context.user_data["target_percentage"] = target_percentage
        try:
            context.bot_data["data"][target_percentage]
        except KeyError:
            context.bot_data["data"][target_percentage] = 2
        back_buttons = [
            build_back_button("back_to_update_percentages"),
            back_to_admin_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text=f"أرسل نسبة {reward_percentages_dict[target_percentage]}، النسبة الحالية هي: <b>{context.bot_data['data'][target_percentage]}%</b>",
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return NEW_PERCENTAGE


back_to_update_percentages = update_percentages


async def new_percentage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        context.bot_data["data"][context.user_data["target_percentage"]] = float(
            update.message.text
        )
        await update.message.reply_text(
            text="تم تعديل نسبة مكافأة الموظفين اليومية بنجاح✅",
            reply_markup=build_admin_keyboard(),
        )
        return ConversationHandler.END


update_percentages_handler = CallbackQueryHandler(
    update_percentages, "^update percentages$"
)


update_percentage_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(update_percentage, "^update.*_percentage$")],
    states={
        NEW_PERCENTAGE: [
            MessageHandler(
                filters=filters.Regex("^\d+$"),
                callback=new_percentage,
            )
        ]
    },
    fallbacks=[back_to_admin_home_page_handler, admin_command],
)

