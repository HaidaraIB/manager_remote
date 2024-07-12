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
    CommandHandler,
)

from common.back_to_home_page import (
    back_to_user_home_page_button,
    back_to_user_home_page_handler,
)
from user.work_with_us.agent import (
    NEIGHBORHOOD,
    LOCATION,
    FRONT_ID,
    BACK_ID,
    REF_NUM,
    choose_gov,
    get_neighborhood,
    share_location,
    get_front_id,
    get_back_id,
    send_to_check_agent_order,
    back_to_get_neighborhood,
    back_to_share_location,
    back_to_get_front_id,
    back_to_get_back_id,
)

from user.work_with_us.common import (
    work_with_us_keyboard,
    WORK_WITH_US_DICT,
    build_govs_keyboard,
)
from common.common import build_back_button
from start import start_command

(
    CHOOSE_WORKING_WITH_US,
    CHOOSE_WHAT_DO_U_WANNA_BE,
    CHOOSE_GOV,
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
            if role == "agent" and not update.effective_user.username:
                await update.callback_query.answer(
                    text="ليس لديك اسم مستخدم علي تيليجرام، يجب عليك اختيار اسم مستخدم لكي تتمكن من تقديم طلب وكيل.",
                    show_alert=True,
                )
                return
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
            govs_keyboard = build_govs_keyboard()
            govs_keyboard.append(back_buttons[0])
            govs_keyboard.append(back_buttons[1])
            await update.callback_query.edit_message_text(
                text="اختر المحافظة التي ستعمل بها",
                reply_markup=InlineKeyboardMarkup(govs_keyboard),
            )
            return CHOOSE_GOV


back_to_choose_what_do_u_wanna_be = choose_working_with_us

back_to_choose_gov = choose_what_do_u_wanna_be

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
        CHOOSE_GOV: [
            CallbackQueryHandler(
                choose_gov,
                "^.+_gov$",
            )
        ],
        NEIGHBORHOOD: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_neighborhood,
            )
        ],
        LOCATION: [
            MessageHandler(
                filters=filters.LOCATION,
                callback=share_location,
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
        REF_NUM: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=send_to_check_agent_order,
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_choose_what_do_u_wanna_be, "^back_to_choose_what_do_u_wanna_be$"
        ),
        CallbackQueryHandler(
            back_to_choose_working_with_us, "^back_to_choose_working_with_us$"
        ),
        CallbackQueryHandler(back_to_get_back_id, "^back_to_get_back_id$"),
        CallbackQueryHandler(back_to_get_front_id, "^back_to_get_front_id$"),
        CallbackQueryHandler(back_to_choose_gov, "^back_to_choose_gov$"),
        CallbackQueryHandler(back_to_share_location, "^back_to_share_location$"),
        CommandHandler("back", back_to_get_neighborhood),
        start_command,
        back_to_user_home_page_handler,
    ],
)
