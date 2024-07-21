from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Chat,
)

from telegram.ext import (
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from models import TrustedAgent, TrustedAgentsOrder
from custom_filters import TeamCash, PromoCode
from common.common import build_back_button
from constants import *
from start import admin_command, start_command
(
    SERIAL,
    TEAM_CASH,
    AFFILIATE,
    NEIGHBORHOOD,
) = range(4)


async def agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        login_button = InlineKeyboardButton(
            text="تسجيل الدخول", callback_data="login_agent"
        )
        if update.message:
            await update.message.reply_text(
                text=AGENT_COMMAND_TEXT,
                reply_markup=InlineKeyboardMarkup.from_button(login_button),
            )
        else:
            await update.callback_query.edit_message_text(
                text=AGENT_COMMAND_TEXT,
                reply_markup=InlineKeyboardMarkup.from_button(login_button),
            )
        return ConversationHandler.END


async def login_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await update.callback_query.edit_message_text(
            text="أرسل الرقم التسلسلي للطلب",
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(text="إلغاء", callback_data="cancel_login_agent")
            ),
        )
        return SERIAL


cancel_login_agent = agent


async def get_serial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if update.message:
            serial = int(update.message.text)
            order = TrustedAgentsOrder.get_one_order(serial=serial)
            agent = TrustedAgent.get_trusted_agents(order_serial=serial)
            if (
                not order
                or order.state != "approved"
                or order.user_id != update.effective_user.id
                or agent
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
                    reply_markup=InlineKeyboardMarkup.from_button(
                        InlineKeyboardButton(text="إلغاء", callback_data="cancel_login_agent")
                    ),
                )
                return
            context.user_data["trusted_agent_order_serial"] = serial
            await update.message.reply_text(
                text=TEAM_CASH_TEXT,
                reply_markup=InlineKeyboardMarkup.from_button(
                    *build_back_button("back_to_get_serial")
                ),
            )
        else:
            await update.callback_query.edit_message_text(
                text=TEAM_CASH_TEXT,
                reply_markup=InlineKeyboardMarkup.from_button(
                    *build_back_button("back_to_get_serial")
                ),
            )

        return TEAM_CASH


back_to_get_serial = login_agent


async def get_team_cash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if update.message:
            team_cash_info = list(
                map(lambda x: x.split(": ")[1], update.message.text.split("\n"))
            )
            context.user_data["team_cash_info"] = team_cash_info
            await update.message.reply_text(
                text=AFFILIATE_TEXT,
                reply_markup=InlineKeyboardMarkup.from_button(
                    *build_back_button("back_to_get_team_cash")
                ),
            )
        else:
            await update.callback_query.edit_message_text(
                text=AFFILIATE_TEXT,
                reply_markup=InlineKeyboardMarkup.from_button(
                    *build_back_button("back_to_get_team_cash")
                ),
            )

        return AFFILIATE


back_to_get_team_cash = get_serial


async def get_affiliate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        affiliate_info = list(
            map(lambda x: x.split(": ")[1], update.message.text.split("\n"))
        )
        context.user_data["affiliate_info"] = affiliate_info
        await update.message.reply_text(
            text="أرسل الآن الحي باللغة الانكليزية كما تم إرساله إليك",
            reply_markup=InlineKeyboardMarkup.from_button(
                *build_back_button("back_to_get_affiliate")
            ),
        )
        return NEIGHBORHOOD


back_to_get_affiliate = get_team_cash


async def get_neighborhood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        team_cash_info = context.user_data["team_cash_info"]
        affiliate_info = context.user_data["affiliate_info"]
        serial = context.user_data["trusted_agent_order_serial"]
        order = TrustedAgentsOrder.get_one_order(serial=serial)

        await TrustedAgent.add_trusted_agent(
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


agent_command = CommandHandler("agent", agent)
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
        admin_command,
        agent_command,
        CallbackQueryHandler(cancel_login_agent, "^cancel_login_agent$"),
        CallbackQueryHandler(back_to_get_affiliate, "^back_to_get_affiliate$"),
        CallbackQueryHandler(back_to_get_serial, "^back_to_get_serial$"),
        CallbackQueryHandler(back_to_get_team_cash, "^back_to_get_team_cash$"),
    ],
)
