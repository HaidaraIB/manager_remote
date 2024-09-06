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
)
from pathlib import Path
import models
from custom_filters import TeamCash, PromoCode
from common.common import build_back_button
from common.back_to_home_page import (
    back_to_agent_home_page_handler,
    back_to_agent_home_page_button,
)
from common.constants import *
from start import start_command, agent_command
import os

(
    SERIAL,
    TEAM_CASH,
    AFFILIATE,
    NEIGHBORHOOD,
) = range(4)


async def login_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await update.callback_query.delete_message()
        await context.bot.send_video(
            chat_id=update.effective_user.id,
            video=os.getenv("LOGIN_GUIDE_VIDEO_ID"),
            caption=LOGIN_GUIDE_TEXT,
            reply_markup=InlineKeyboardMarkup(back_to_agent_home_page_button),
        )
        return SERIAL


async def get_serial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_get_serial"),
            back_to_agent_home_page_button[0],
        ]
        if update.message:
            serial = int(update.message.text)
            order = models.WorkWithUsOrder.get_one_order(serial=serial)
            ag = models.TrustedAgent.get_workers(order_serial=serial)
            if (
                not order
                or order.state == "deleted"
                or order.state != "approved"
                or order.user_id != update.effective_user.id
                or ag
                or (not ag and order.state == "approved")
            ):
                await update.message.reply_text(
                    text=(
                        "حدث خطأ ما، يحدث هذا عادةً للأسباب التالية:\n"
                        "1 - رقم تسلسلي خاطئ\n"
                        "2 - الطلب قيد المراجعة\n"
                        "3 - لست من قام بتقديم هذا الطلب\n"
                        "4 - هذا الطلب قد تم تسجيل الدخول باستخدامه بالفعل.\n\n"
                        "تحقق من الأمر وأعد المحاولة."
                    ),
                    reply_markup=InlineKeyboardMarkup(back_to_agent_home_page_button),
                )
                return
            context.user_data["trusted_agent_order_serial"] = serial
            await update.message.reply_text(
                text=TEAM_CASH_TEXT,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEAM_CASH_TEXT,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )

        return TEAM_CASH


back_to_get_serial = login_agent


async def get_team_cash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_get_team_cash"),
            back_to_agent_home_page_button[0],
        ]
        if update.message:

            if "User ID: Someone" in update.message.text:
                await update.message.reply_text(text="الرجاء إرسال معلومات صحيحة ❗️")
                return

            team_cash_info = list(
                map(lambda x: x.split(": ")[1], update.message.text.split("\n"))
            )
            context.user_data["team_cash_info"] = team_cash_info
        else:
            await update.callback_query.delete_message()
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=AFFILIATE_TEXT,
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return AFFILIATE


back_to_get_team_cash = get_serial


async def get_affiliate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_get_affiliate"),
            back_to_agent_home_page_button[0],
        ]
        affiliate_info = list(
            map(lambda x: x.split(": ")[1], update.message.text.split("\n"))
        )
        context.user_data["affiliate_info"] = affiliate_info
        await update.message.reply_photo(
            photo=Path("assets/show_agent_sample.jpg"),
            caption="أرسل الآن الاسم الذي تريد أن يظهر في قائمة الوكلاء الموصى بهم",
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return NEIGHBORHOOD


back_to_get_affiliate = get_team_cash


async def get_neighborhood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        team_cash_info = context.user_data["team_cash_info"]
        affiliate_info = context.user_data["affiliate_info"]
        serial = context.user_data["trusted_agent_order_serial"]
        order = models.WorkWithUsOrder.get_one_order(serial=serial)

        await models.TrustedAgent.add_trusted_agent(
            user_id=update.effective_user.id,
            order_serial=serial,
            gov=order.gov,
            neighborhood=update.message.text,
            team_cash_user_id=team_cash_info[0],
            team_cash_password=team_cash_info[1],
            team_cash_workplace_id=team_cash_info[2],
            promo_username=affiliate_info[0],
            promo_password=affiliate_info[1],
        )

        await update.message.reply_text(text="تم تسجيل الدخول بنجاح ✅")
        return ConversationHandler.END


login_agent_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(login_agent, "^login_agent$")],
    states={
        SERIAL: [
            MessageHandler(
                filters=filters.Regex("^\d+$"),
                callback=get_serial,
            )
        ],
        TEAM_CASH: [
            MessageHandler(
                filters=TeamCash(),
                callback=get_team_cash,
            )
        ],
        AFFILIATE: [
            MessageHandler(
                filters=PromoCode(),
                callback=get_affiliate,
            )
        ],
        NEIGHBORHOOD: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_neighborhood,
            )
        ],
    },
    fallbacks=[
        start_command,
        agent_command,
        back_to_agent_home_page_handler,
        CallbackQueryHandler(back_to_get_affiliate, "^back_to_get_affiliate$"),
        CallbackQueryHandler(back_to_get_serial, "^back_to_get_serial$"),
        CallbackQueryHandler(back_to_get_team_cash, "^back_to_get_team_cash$"),
    ],
    name="agent_login_conversation",
    persistent=True,
)
