from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Chat,
)

from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from user.work_with_us.common import syrian_govs_en_ar
from check_work_with_us.common import (
    create_promo_code_invalid_foramt_login_info,
    create_team_cash_invalid_foramt_login_info,
)
from custom_filters import AgentOrder, TeamCash, PromoCode
from DB import DB
import os


async def accept_agent_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        serial = update.callback_query.data.split("_")[-1]
        await update.callback_query.answer(
            text=("قم بالرد على هذه الرسالة بمعلومات تسجيل الدخول"),
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن قبول الطلب 🔙",
                    callback_data=f"back_from_accept_trusted_agent_order_{update.effective_user.id}_{serial}",
                )
            )
        )


async def get_login_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data.split("_")
        manager_id = int(data[-2])

        if update.effective_user.id != manager_id or (
            update.effective_chat.id
            not in [
                context.bot_data["data"]["partner_orders_group"],
                context.bot_data["data"]["agent_orders_group"],
            ]
        ):
            return

        serial = int(data[-1])
        order = DB.get_one_order(order_type="trusted_agents", serial=serial)

        if (
            update.effective_chat.id == context.bot_data["data"]["agent_orders_group"]
            and len(update.message.text_html.split("\n")) == 2
        ):
            await update.message.reply_text(
                text=create_team_cash_invalid_foramt_login_info()
            )
            return

        elif (
            update.effective_chat.id == context.bot_data["data"]["partner_orders_group"]
            and len(update.message.text_html.split("\n")) == 3
        ):
            await update.message.reply_text(
                text=create_promo_code_invalid_foramt_login_info()
            )
            return

        if not context.chat_data.get(f"trusted_agent_orders_{serial}", False):
            context.chat_data[f"trusted_agent_orders_{serial}"] = (
                update.message.text_html
            )

        else:
            team_cash_caption = (
                update.message.text_html
                if len(update.message.text_html.split("\n")) == 3
                else context.chat_data[f"trusted_agent_orders_{serial}"]
            )
            promo_code_caption = (
                update.message.text_html
                if len(update.message.text_html.split("\n")) == 2
                else context.chat_data[f"trusted_agent_orders_{serial}"]
            )
            await DB.add_trusted_agent(
                user_id=order["user_id"],
                order_serial=serial,
                gov=order["gov"],
                team_cash_user_id=team_cash_caption.split("\n")[0].split(" : ")[1],
                team_cash_password=team_cash_caption.split("\n")[1].split(" : ")[1],
                team_cash_workplace_id=team_cash_caption.split("\n")[2].split(" : ")[1],
                promo_username=promo_code_caption.split("\n")[0].split(" : ")[1],
                promo_password=promo_code_caption.split("\n")[1].split(" : ")[1],
            )
            await context.bot.send_message(
                chat_id=order["user_id"],
                text=(
                    f"مبروك، تمت الموافقة على طلبك للعمل معنا كوكيل لمحافظة <b>{syrian_govs_en_ar[order['gov']]}</b>\n\n"
                    "سيظهر زر يؤدي إلى حسابك الشخصي بين قائمة الوكلاء الموصى بهم في محافظتك من الآن فصاعداً.\n\n"
                    f"الرقم التسلسلي للطلب: <code>{serial}</code>\n\n"
                ),
            )
            await context.bot.send_document(
                chat_id=order["user_id"],
                document=os.getenv("TEAM_CASH_ID"),
                caption="تطبيق شحن وسحب أرصدة اللاعبين:\n\n"
                + "معلومات تسجيل الدخول:\n\n"
                + team_cash_caption,
            )
            await context.bot.send_document(
                chat_id=order["user_id"],
                document=os.getenv("PROMO_CODE_ID"),
                caption="تطبيق استلام الأرباح من خسائر اللاعبين:\n\n"
                + "معلومات تسجيل الدخول:\n\n"
                + promo_code_caption,
            )
        await update.message.reply_to_message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تمت الموافقة ✅", callback_data="تمت الموافقة ✅"
                )
            )
        )


async def invalid_login_info_agent_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data.split("_")
        manager_id = int(data[-2])

        if update.effective_user.id != manager_id or (
            update.effective_chat.id
            not in [
                context.bot_data["data"]["partner_orders_group"],
                context.bot_data["data"]["agent_orders_group"],
            ]
        ):
            return

        if update.effective_chat.id == context.bot_data["data"]["agent_orders_group"]:
            await update.message.reply_text(
                text=create_team_cash_invalid_foramt_login_info()
            )

        elif (
            update.effective_chat.id == context.bot_data["data"]["partner_orders_group"]
        ):
            await update.message.reply_text(
                text=create_promo_code_invalid_foramt_login_info()
            )


accept_agent_order_handler = CallbackQueryHandler(
    accept_agent_order, "^accept_agent_order_\d+$"
)

invalid_login_info_agent_order_handler = MessageHandler(
    filters=AgentOrder() & filters.REPLY & (~TeamCash() | ~PromoCode()),
    callback=invalid_login_info_agent_order,
)

get_apk_login_info_handler = MessageHandler(
    filters=AgentOrder() & filters.REPLY & (TeamCash() | PromoCode()),
    callback=get_login_info,
)
