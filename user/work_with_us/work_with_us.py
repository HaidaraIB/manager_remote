from telegram import (
    Update,
    InlineKeyboardMarkup,
    Chat,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    CommandHandler
)

from common.back_to_home_page import (
    back_to_user_home_page_button,
    back_to_user_home_page_handler,
)
from user.work_with_us.agent import (
    FRONT_ID,
    BACK_ID,
    PRE_BALANCE,
    WITHDRAW_NAME,
    GOV,
    LOCATION,
    get_full_name,
    share_location,
    get_back_id,
    get_front_id,
    get_gov,
    get_pre_balance,
    get_withdraw_name,
    back_to_get_back_id,
    back_to_get_front_id,
    back_to_get_gov,
    back_to_get_pre_balance,
    back_to_get_withdraw_name,
)

from user.work_with_us.common import work_with_us_keyboard, WORK_WITH_US_DICT
from common.common import build_back_button
from start import start_command

(
    CHOOSE_WORKING_WITH_US,
    CHOOSE_WHAT_DO_U_WANNA_BE,
    FULL_NAME,
) = range(3)


async def work_with_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await update.callback_query.edit_message_text(
            text="عملك معنا",
            reply_markup=InlineKeyboardMarkup(work_with_us_keyboard),
        )
        return CHOOSE_WORKING_WITH_US


async def choose_working_with_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not update.callback_query.data.startswith("back"):
            role = update.callback_query.data.split("_")[0]
            context.user_data["work_with_us_role"] = role
        else:
            role = context.user_data["work_with_us_role"]
        choose_working_with_us_keyboard = [
            [WORK_WITH_US_DICT[role]["button"]],
            build_back_button("back_to_choose_working_with_us"),
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text=WORK_WITH_US_DICT[role]["text"],
            reply_markup=InlineKeyboardMarkup(choose_working_with_us_keyboard),
        )
        return CHOOSE_WHAT_DO_U_WANNA_BE

back_to_choose_working_with_us = work_with_us

async def choose_what_do_u_wanna_be(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_choose_what_do_u_wanna_be"),
            back_to_user_home_page_button[0],
        ]
        if context.user_data["work_with_us_role"] == "agent":
            await update.callback_query.edit_message_text(
                text="أرسل اسمك الثلاثي",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return FULL_NAME

back_to_choose_what_do_u_wanna_be = choose_working_with_us

back_to_get_full_name = choose_what_do_u_wanna_be

work_with_us_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            work_with_us,
            "^work with us$",
        ),
    ],
    states={
        CHOOSE_WORKING_WITH_US: [
            CallbackQueryHandler(
                choose_working_with_us,
                "^((agent)|(partner))_work_with_us$",
            ),
        ],
        CHOOSE_WHAT_DO_U_WANNA_BE: [
            CallbackQueryHandler(
                choose_what_do_u_wanna_be,
                "^wanna_be_((agent)|(partner))$",
            )
        ],
        FULL_NAME: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_full_name,
            )
        ],
        FRONT_ID: [
            MessageHandler(
                filters=filters.PHOTO,
                callback=get_front_id,
            )
        ],
        BACK_ID: [
            MessageHandler(
                filters=filters.PHOTO,
                callback=get_back_id,
            )
        ],
        PRE_BALANCE: [
            MessageHandler(
                filters=filters.Regex("^\d+.?\d*$"),
                callback=get_pre_balance,
            )
        ],
        WITHDRAW_NAME: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_withdraw_name,
            )
        ],
        GOV: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_gov,
            )
        ],
        LOCATION: [
            MessageHandler(
                filters=filters.LOCATION,
                callback=share_location,
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_get_pre_balance, "^back_to_get_pre_balance$"),
        CallbackQueryHandler(back_to_choose_what_do_u_wanna_be, "^back_to_choose_what_do_u_wanna_be$"),
        CallbackQueryHandler(back_to_choose_working_with_us, "^back_to_choose_working_with_us$"),
        CallbackQueryHandler(back_to_get_back_id, "^back_to_get_back_id$"),
        CallbackQueryHandler(back_to_get_front_id, "^back_to_get_front_id$"),
        CallbackQueryHandler(back_to_get_full_name, "^back_to_get_full_name$"),
        CallbackQueryHandler(back_to_get_gov, "^back_to_get_gov$"),
        CommandHandler('back', back_to_get_withdraw_name),
        start_command,
        back_to_user_home_page_handler,
    ],
    
)
