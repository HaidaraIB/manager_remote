from telegram import Chat, Update, InlineKeyboardMarkup, InlineKeyboardButton
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
from start import admin_command
from custom_filters import Admin

NEW_PERCENTAGE = 0


async def update_percentages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        keyboard = [
            [
                InlineKeyboardButton(
                    text="تعديل نسبة مكافأة الموظفين الأسبوعية 🧑🏻‍💻",
                    callback_data="update workers_reward_percentage",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="تعديل نسبة مكافأة الموظفين اليومية 🧑🏻‍💻",
                    callback_data="update workers_reward_withdraw_percentage",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="تعديل مجموع مبالغ إيداع إنشاء الحسابات 🎁",
                    callback_data="update create_account_deposit_pin",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="تعديل مبلغ ساعة الحظ 🕐",
                    callback_data="update lucky_hour_amount",
                ),
            ],
            back_to_admin_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="اختر النسبة التي تريد تعديلها:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ConversationHandler.END


reward_percentages_dict = {
    "workers_reward_withdraw_percentage": "نسبة مكافأة الموظفين اليومية",
    "workers_reward_percentage": "نسبة مكافأة الموظفين الأسبوعية",
    "deposit_gift_percentage": "نسبة مكافأة الإيداع",
    "create_account_deposit_pin": "قيمة مبالغ إيداع إنشاء الحسابات",
    "lucky_hour_amount": "قيمة مبلغ ساعة الحظ",
}


async def update_percentage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        target_percentage = update.callback_query.data.replace("update ", "")
        context.user_data["target_percentage"] = target_percentage
        try:
            context.bot_data[target_percentage]
        except KeyError:
            context.bot_data[target_percentage] = 0
        back_buttons = [
            build_back_button("back_to_update_percentages"),
            back_to_admin_home_page_button[0],
        ]
        
        create_account_deposit_left_over_line = ""
        if target_percentage == "create_account_deposit_pin":
            create_account_deposit_left_over_line = f"بقي منها: <b>{context.bot_data.get('create_account_deposit', 0)}</b>\n"

        await update.callback_query.edit_message_text(
            text=(
                f"أرسل {reward_percentages_dict[target_percentage]} الجديدة\n"
                + f"القيمة الحالية هي: <b>{context.bot_data[target_percentage]}</b>\n"
                + create_account_deposit_left_over_line
            ),
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )

        return NEW_PERCENTAGE


back_to_update_percentages = update_percentages


async def new_percentage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        target_percentage = context.user_data["target_percentage"]
        val = float(update.message.text)

        context.bot_data[target_percentage] = val
        if target_percentage.endswith("pin"):
            context.bot_data["create_account_deposit"] = val

        await update.message.reply_text(
            text=f"تم تعديل {reward_percentages_dict[target_percentage]} بنجاح✅",
            reply_markup=build_admin_keyboard(),
        )
        return ConversationHandler.END


update_percentages_handler = CallbackQueryHandler(
    update_percentages, "^update percentages$"
)


update_percentage_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            update_percentage,
            "^update.*_((percentage)|(pin)|(amount))$",
        ),
    ],
    states={
        NEW_PERCENTAGE: [
            MessageHandler(
                filters=filters.Regex("^\d+$"),
                callback=new_percentage,
            )
        ]
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_update_percentages,
            "^back_to_update_percentages$",
        ),
        back_to_admin_home_page_handler,
        admin_command,
    ],
)
