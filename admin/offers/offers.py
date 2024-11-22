from telegram import Update, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
import jobs
from custom_filters import Admin
from common.back_to_home_page import (
    back_to_admin_home_page_button,
    back_to_admin_home_page_handler,
)
from common.common import build_back_button, build_admin_keyboard, format_amount
from common.stringifies import order_settings_dict, stringify_offer
from common.constants import TIMEZONE
from admin.offers.common import get_offer_info
from start import admin_command
import datetime

ORDER_TYPE, TOTAL, PERCENTAGE, DATE, MIN, MAX = range(6)


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
        total, p, d, min_amount, max_amount, _ = get_offer_info(context, order_type)
        if total:
            old_offer_text = (
                f"\n\n<b>تنبيه</b> "
                f"هناك عرض {order_settings_dict[order_type]['t']} حالي:\n"
                + stringify_offer(total, p, d, min_amount, max_amount)
                + f"العرض الجديد سيحل محله."
            )
        back_buttons = [
            build_back_button("back_to_choose_order_type"),
            back_to_admin_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="أرسل المبلغ الإجمالي" + old_offer_text,
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return TOTAL


back_to_choose_order_type = offers


async def get_total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        order_type = context.user_data["offer_order_type"]
        back_buttons = [
            build_back_button("back_to_get_total"),
            back_to_admin_home_page_button[0],
        ]
        if update.message:
            total = float(update.message.text)
            context.user_data[f"{order_type}_offer_total"] = total
            await update.message.reply_text(
                text="أرسل النسبة",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text="أرسل النسبة",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )

        return PERCENTAGE


back_to_get_total = choose_order_type


async def get_percentage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        back_buttons = [
            build_back_button("back_to_get_percentage"),
            back_to_admin_home_page_button[0],
        ]
        order_type = context.user_data["offer_order_type"]
        if update.message:
            p = float(update.message.text)
            context.user_data[f"{order_type}_offer_percentage"] = p
            await update.message.reply_text(
                text=(
                    "أرسل تاريخ بدء العرض بالتنسيق التالي:\n"
                    "<code>YYYY-MM-DD HH:MM</code>\n"
                    "مثال:\n"
                    "<code>2024-11-22 14:13</code>"
                ),
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text=(
                    "أرسل تاريخ بدء العرض بالتنسيق التالي: YYYY-MM-DD HH:MM\n"
                    "مثال:\n2024-11-22 14:13"
                ),
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return DATE


back_to_get_percentage = get_total


async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        back_buttons = [
            build_back_button("back_to_get_date"),
            back_to_admin_home_page_button[0],
        ]
        order_type = context.user_data["offer_order_type"]
        if update.message:
            d = datetime.datetime.strptime(
                update.message.text, "%Y-%m-%d %H:%M"
            ).astimezone(tz=TIMEZONE)
            now = datetime.datetime.now(TIMEZONE)
            if now >= d:
                back_to_get_percentage_buttons = [
                    build_back_button("back_to_get_percentage"),
                    back_to_admin_home_page_button[0],
                ]
                await update.message.reply_text(
                    text="الرجاء إرسال موعد في المستقبل ❗️",
                    reply_markup=InlineKeyboardMarkup(back_to_get_percentage_buttons),
                )
                return

            context.user_data[f"{order_type}_offer_date"] = d
            await update.message.reply_text(
                text="أرسل الحد الأدنى لمبلغ المستفيد",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text="أرسل الحد الأدنى لمبلغ المستفيد",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return MIN


back_to_get_date = get_percentage


async def get_min(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        back_buttons = [
            build_back_button("back_to_get_min"),
            back_to_admin_home_page_button[0],
        ]
        order_type = context.user_data["offer_order_type"]
        if update.message:
            min_amount = float(update.message.text)
            context.user_data[f"{order_type}_offer_min_amount"] = min_amount
            await update.message.reply_text(
                text="أرسل الحد الأعلى لمبلغ المستفيد",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text="أرسل الحد الأعلى لمبلغ المستفيد",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return MAX


back_to_get_min = get_date


async def get_max(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        order_type = context.user_data["offer_order_type"]

        # getting temp offer values
        total = context.user_data[f"{order_type}_offer_total"]
        p = context.user_data[f"{order_type}_offer_percentage"]
        d: datetime = context.user_data[f"{order_type}_offer_date"]
        min_amount = context.user_data[f"{order_type}_offer_min_amount"]
        max_amount = float(update.message.text)
        job_name = f"{order_type}_offer"
        offer_jobs = context.job_queue.get_jobs_by_name(job_name)
        if offer_jobs:
            offer_jobs[0].schedule_removal()
        context.job_queue.run_once(
            callback=jobs.start_offer,
            when=d,
            name=job_name,
            data={
                "total": total,
                "p": p,
                "d": d,
                "min_amount": min_amount,
                "max_amount": max_amount,
            },
            job_kwargs={
                "id": job_name,
                "coalesce": True,
                "replace_existing": True,
                "misfire_grace_time": None,
            },
        )
        await update.message.reply_text(
            text=(
                f"تم تحديث عرض ال{order_settings_dict[order_type]['t']}:\n"
                + stringify_offer(total, p, d, min_amount, max_amount)
            ),
            reply_markup=build_admin_keyboard(),
        )
        return ConversationHandler.END


offers_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            offers,
            "^offers$",
        )
    ],
    states={
        ORDER_TYPE: [
            CallbackQueryHandler(
                choose_order_type,
                "^((withdraw)|(deposit))_offer$",
            )
        ],
        TOTAL: [
            MessageHandler(
                filters=filters.Regex("^[0-9]+\.?[0-9]*$"),
                callback=get_total,
            )
        ],
        PERCENTAGE: [
            MessageHandler(
                filters=filters.Regex("^[0-9]+\.?[0-9]*$"),
                callback=get_percentage,
            )
        ],
        DATE: [
            MessageHandler(
                filters=filters.Regex("^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$"),
                callback=get_date,
            )
        ],
        MIN: [
            MessageHandler(
                filters=filters.Regex("^[0-9]+\.?[0-9]*$"),
                callback=get_min,
            )
        ],
        MAX: [
            MessageHandler(
                filters=filters.Regex("^[0-9]+\.?[0-9]*$"),
                callback=get_max,
            )
        ],
    },
    fallbacks=[
        admin_command,
        back_to_admin_home_page_handler,
        CallbackQueryHandler(back_to_choose_order_type, "^back_to_choose_order_type$"),
        CallbackQueryHandler(back_to_get_total, "^back_to_get_total$"),
        CallbackQueryHandler(back_to_get_percentage, "^back_to_get_percentage$"),
        CallbackQueryHandler(back_to_get_date, "^back_to_get_date$"),
        CallbackQueryHandler(back_to_get_min, "^back_to_get_min$"),
    ],
)
