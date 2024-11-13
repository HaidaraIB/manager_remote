from telegram import Update, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from jobs import reset_offer_percentage
from custom_filters import Admin
from common.back_to_home_page import (
    back_to_admin_home_page_button,
    back_to_admin_home_page_handler,
)
from common.common import build_back_button, build_admin_keyboard, calc_period
from common.stringifies import order_settings_dict
import datetime
from start import admin_command

ORDER_TYPE, PERCENTAGE, PERIOD = range(3)


async def offers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        keyboard = [
            [
                InlineKeyboardButton(
                    text="سحب 💳",
                    callback_data="withdraw_offer",
                ),
                InlineKeyboardButton(
                    text="إيداع 📥",
                    callback_data="deposit_offer",
                ),
            ],
            back_to_admin_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="اختر نوع العرض",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ORDER_TYPE


async def choose_order_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if not update.callback_query.data.startswith("back"):
            order_type = update.callback_query.data.replace("_offer", "")
            context.user_data["offer_order_type"] = order_type
        else:
            order_type = context.user_data["offer_order_type"]

        old_offer_text = ""
        offer_job = context.job_queue.get_jobs_by_name(f"{order_type}_offer")
        if offer_job:
            diff = offer_job[0].next_t - datetime.datetime.now()
            seconds = diff.total_seconds() - (2 * 24 * 60 * 60)
            old_offer_text = (
                f"\n\nملاحظة: هناك عرض {order_settings_dict[order_type]['t']}"
                f" بنسبة {context.bot_data[f'{order_type}_offer_percentage']}%"
                f" سينتهي بعد {calc_period(abs(seconds))}"
                f" العرض الجديد سيحل محله."
            )
        back_buttons = [
            build_back_button("back_to_choose_order_type"),
            back_to_admin_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="أرسل النسبة" + old_offer_text,
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return PERCENTAGE


back_to_choose_order_type = offers


async def get_percentage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        p = float(update.message.text)
        context.bot_data[f"offer_percentage"] = p
        back_buttons = [
            build_back_button("back_to_get_percentage"),
            back_to_admin_home_page_button[0],
        ]
        await update.message.reply_text(
            text="أرسل المدة بالساعة",
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return PERIOD


back_to_get_percentage = choose_order_type


async def get_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        t = float(update.message.text)
        order_type = context.user_data["offer_order_type"]
        p = context.bot_data[f"offer_percentage"]
        job_name = f"{order_type}_offer"
        offer_jobs = context.job_queue.get_jobs_by_name(job_name)
        if offer_jobs:
            offer_jobs[0].schedule_removal()
        context.job_queue.run_once(
            callback=reset_offer_percentage,
            when=t * 60 * 60,
            name=job_name,
            data={"p": p, "t": t},
            job_kwargs={
                "id": job_name,
                "coalesce": True,
                "replace_existing": True,
            },
        )
        await update.message.reply_text(
            text=f"تم تحديث نسبة عرض ال{order_settings_dict[order_type]['t']} إلى {p}% لمدة {t} ساعة.",
            reply_markup=build_admin_keyboard(),
        )
        return ConversationHandler.END


offers_handler  = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            offers,
            "offers",
        )
    ],
    states={
        ORDER_TYPE: [
            CallbackQueryHandler(
                choose_order_type,
                "^((withdraw)|(deposit))_offer$",
            )
        ],
        PERCENTAGE: [
            MessageHandler(
                filters=filters.Regex("^[0-9]+\.[0-9]*$"),
                callback=get_percentage,
            )
        ],
        PERIOD: [
            MessageHandler(
                filters=filters.Regex("^[0-9]+\.[0-9]*$"),
                callback=get_period,
            ) 
        ]
    },
    fallbacks=[
        admin_command,
        back_to_admin_home_page_handler,
        CallbackQueryHandler(
            back_to_choose_order_type, "^back_to_choose_order_type$"
        ),
        CallbackQueryHandler(
            back_to_get_percentage, "^back_to_get_percentage$"
        )
    ]
)