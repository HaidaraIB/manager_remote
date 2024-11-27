from telegram import Update, Chat, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from common.back_to_home_page import (
    back_to_user_home_page_button,
    back_to_user_home_page_handler,
)
from common.constants import *
from common.common import build_back_button, build_user_keyboard
from user.user_settings.common import build_user_settings_keyboard
from start import start_command
import models
from datetime import datetime

(
    CHOOSE_SETTING,
    BANK,
    CREATE_BANK_ACCOUNT,
    FULL_NAME,
    CHOOSE_BANK_ACCOUNT_SETTING,
    NEW_BANK_ACCOUNT_NUMBER,
    NEW_BANK_ACCOUNT_FULL_NAME,
) = range(7)


async def user_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        keyboard = build_user_settings_keyboard()
        keyboard.append(back_to_user_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="الإعدادات",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CHOOSE_SETTING


async def choose_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not update.callback_query.data.startswith("back"):
            chosen_setting = update.callback_query.data
            context.user_data["chosen_setting"] = chosen_setting
        else:
            chosen_setting = context.user_data["chosen_setting"]
        if chosen_setting.startswith("bank_accounts"):
            banks_keyboard = [
                [
                    InlineKeyboardButton(
                        text=BEMO,
                        callback_data=BEMO,
                    ),
                    InlineKeyboardButton(
                        text=BARAKAH,
                        callback_data=BARAKAH,
                    ),
                ],
                build_back_button("back_to_choose_setting"),
                back_to_user_home_page_button[0],
            ]
            await update.callback_query.edit_message_text(
                text="اختر البنك",
                reply_markup=InlineKeyboardMarkup(banks_keyboard),
            )
            return BANK


back_to_choose_setting = user_settings


async def choose_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not update.callback_query.data.startswith("back"):
            chosen_bank = update.callback_query.data
            context.user_data["chosen_bank"] = chosen_bank
        else:
            chosen_bank = context.user_data["chosen_bank"]
        bank = models.BankAccount.get(
            user_id=update.effective_user.id, bank=chosen_bank
        )
        back_buttons = [
            build_back_button("back_to_choose_bank"),
            back_to_user_home_page_button[0],
        ]
        if not bank:
            await update.callback_query.edit_message_text(
                text=(
                    f"ليس لديك حساب <b>{chosen_bank}</b> بعد\n"
                    "أرسل رقم الحساب لإنشائه."
                ),
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return CREATE_BANK_ACCOUNT

        bank_accounts_settings_keyboard = [
            [
                InlineKeyboardButton(
                    text="تغيير رقم الحساب",
                    callback_data=f"update_bank_account_number",
                ),
                InlineKeyboardButton(
                    text="تغيير الاسم",
                    callback_data=f"update_bank_account_full_name",
                ),
            ],
            *back_buttons,
        ]
        await update.callback_query.edit_message_text(
            text=(
                f"<b>بنك {chosen_bank}</b>\n"
                f"رقم الحساب: <code>{bank.bank_account_number}</code>\n"
                f"الاسم: <b>{bank.full_name}</b>"
            ),
            reply_markup=InlineKeyboardMarkup(bank_accounts_settings_keyboard),
        )
        return CHOOSE_BANK_ACCOUNT_SETTING


async def create_bank_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        bank_account_number = update.message.text
        context.user_data["bank_account_number"] = bank_account_number
        bank_account = models.BankAccount.get(bank_account_number=bank_account_number)
        if bank_account:
            back_buttons = [
                build_back_button("back_to_choose_bank"),
                back_to_user_home_page_button[0],
            ]
            await update.message.reply_text(
                text="رقم الحساب هذا موجود لدينا مسبقاً ❗️",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return
        back_buttons = [
            build_back_button("back_to_create_bank_account"),
            back_to_user_home_page_button[0],
        ]
        await update.message.reply_text(
            text="أرسل الاسم الكامل لصاحب هذا الحساب",
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return FULL_NAME


back_to_create_bank_account = choose_bank


async def get_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        full_name = update.message.text
        chosen_bank = context.user_data["chosen_bank"]
        bank_account_number = context.user_data["bank_account_number"]
        await models.BankAccount.add(
            user_id=update.effective_user.id,
            bank_account_number=bank_account_number,
            bank=chosen_bank,
            full_name=full_name,
        )
        await update.message.reply_text(
            text=(
                f"تم إنشاء حساب <b>{chosen_bank}</b>\n"
                f"رقم الحساب: <code>{bank_account_number}</code>\n"
                f"الاسم: <b>{full_name}</b>"
            ),
            reply_markup=build_user_keyboard(),
        )
        return ConversationHandler.END


back_to_choose_bank = choose_setting


async def choose_bank_account_setting(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE:
        await update.callback_query.answer(
            text="لتعديل معلومات الحساب تحتاج إلى موافقة الإدارة ❗️",
            show_alert=True,
        )
        return
        if not update.callback_query.data.startswith("back"):
            chosen_bank_account_setting = update.callback_query.data
            context.user_data["chosen_bank_account_setting"] = (
                chosen_bank_account_setting
            )
        else:
            chosen_bank_account_setting = context.user_data[
                "chosen_bank_account_setting"
            ]
        back_buttons = [
            build_back_button("back_to_choose_bank_account_setting"),
            back_to_user_home_page_button[0],
        ]
        chosen_bank = context.user_data["chosen_bank"]
        bank = models.BankAccount.get(
            user_id=update.effective_user.id, bank=chosen_bank
        )
        if chosen_bank_account_setting == "update_bank_account_number":
            await update.callback_query.edit_message_text(
                text=(
                    f"أرسل رقم حساب <b>{chosen_bank}</b>\n"
                    f"الرقم الحالي: <code>{bank.bank_account_number}</code>"
                ),
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return NEW_BANK_ACCOUNT_NUMBER
        elif chosen_bank_account_setting == "update_bank_account_full_name":
            await update.callback_query.edit_message_text(
                text=(
                    f"أرسل الاسم الجديد لحساب <b>{chosen_bank}</b>\n"
                    f"الاسم الحالي: <code>{bank.full_name}</code>"
                ),
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return NEW_BANK_ACCOUNT_FULL_NAME


back_to_choose_bank_account_setting = choose_bank


async def get_new_bank_account_full_name(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE:
        full_name = update.message.text
        chosen_bank = context.user_data["chosen_bank"]
        await models.BankAccount.update(
            user_id=update.effective_user.id,
            bank=chosen_bank,
            field="full_name",
            value=full_name,
        )
        await update.message.reply_text(
            text=f"تم تعديل اسم صاحب حساب <b>{chosen_bank}</b> بنجاح ✅",
            reply_markup=build_user_keyboard(),
        )
        return ConversationHandler.END


async def get_new_bank_account_number(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE:
        new_bank_account_number = update.message.text
        bank_account = models.BankAccount.get(
            bank_account_number=new_bank_account_number
        )
        if bank_account:
            back_buttons = [
                build_back_button("back_to_choose_bank_account_setting"),
                back_to_user_home_page_button[0],
            ]
            await update.message.reply_text(
                text="رقم الحساب هذا موجود لدينا مسبقاً ❗️",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return
        chosen_bank = context.user_data["chosen_bank"]
        await models.BankAccount.update(
            user_id=update.effective_user.id,
            bank=chosen_bank,
            field="bank_account_number",
            value=new_bank_account_number,
        )
        await update.message.reply_text(
            text=f"تم تعديل رقم حساب <b>{chosen_bank}</b> بنجاح ✅",
            reply_markup=build_user_keyboard(),
        )
        return ConversationHandler.END


user_settings_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(user_settings, "^user_settings$")],
    states={
        CHOOSE_SETTING: [
            CallbackQueryHandler(
                choose_setting,
                "^bank_accounts_settings$",
            )
        ],
        BANK: [
            CallbackQueryHandler(
                choose_bank,
                lambda x: x in BANKS,
            )
        ],
        CREATE_BANK_ACCOUNT: [
            MessageHandler(
                filters=filters.Regex("^[0-9]+$"),
                callback=create_bank_account,
            )
        ],
        FULL_NAME: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_full_name,
            )
        ],
        CHOOSE_BANK_ACCOUNT_SETTING: [
            CallbackQueryHandler(
                choose_bank_account_setting,
                "^update_bank_account_((number)|(full_name))$",
            )
        ],
        NEW_BANK_ACCOUNT_NUMBER: [
            MessageHandler(
                filters=filters.Regex("^[0-9]+$"),
                callback=get_new_bank_account_number,
            )
        ],
        NEW_BANK_ACCOUNT_FULL_NAME: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_new_bank_account_full_name,
            )
        ],
    },
    fallbacks=[
        start_command,
        back_to_user_home_page_handler,
        CallbackQueryHandler(back_to_choose_setting, "^back_to_choose_setting$"),
        CallbackQueryHandler(back_to_choose_bank, "^back_to_choose_bank$"),
        CallbackQueryHandler(
            back_to_create_bank_account, "^back_to_create_bank_account$"
        ),
        CallbackQueryHandler(
            back_to_choose_bank_account_setting, "^back_to_choose_bank_account_setting$"
        ),
    ],
)
