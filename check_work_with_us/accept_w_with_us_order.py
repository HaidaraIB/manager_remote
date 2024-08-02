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

from user.work_with_us.common import syrian_govs_en_ar, stringify_w_with_us_order
from custom_filters import AgentOrder, Declined
from common.common import build_agent_keyboard
from constants import *
import os
import models


async def notify_w_with_us_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:

        data = update.callback_query.data.split("_")
        serial = int(data[-1])
        role = data[-2]

        if context.bot_data.get(f"notified_{role}_order_{serial}", False):
            await update.callback_query.answer(
                "تم الإشعار بالفعل",
                show_alert=True,
            )
            return

        order = models.WorkWithUsOrder.get_one_order(serial=serial)
        await context.bot.send_message(
            chat_id=order.user_id,
            text=(
                "تم استلام الدفعة الخاصة بطلب الوكيل المقدم من قبلك وسيتم تنفيذ طلبك خلال 5 أيام عمل\n\n"
                + "تفاصيل الطلب:\n\n"
                + stringify_w_with_us_order(
                    gov=syrian_govs_en_ar[order.gov],
                    neighborhood=order.neighborhood,
                    amount=order.amount,
                    email=order.email,
                    phone=order.phone,
                    ref_num=order.ref_number,
                    serial=serial,
                )
            ),
        )
        await update.callback_query.answer(
            "تم ✅",
            show_alert=True,
        )
        context.bot_data[f"notified_{role}_order_{serial}"] = True


async def accept_w_with_us_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        data = update.callback_query.data.split("_")
        serial = int(data[-1])
        role = data[-2]
        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بمعلومات تسجيل الدخول",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن قبول الطلب 🔙",
                    callback_data=f"back_from_accept_{role}_{update.effective_user.id}_{serial}",
                )
            )
        )


async def get_login_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data.split("_")

        serial = int(data[-1])
        role = data[-2]
        order = models.WorkWithUsOrder.get_one_order(serial=serial)

        if role == "agent":
            context.chat_data[f"trusted_agent_orders_{serial}"] = (
                update.message.text_html
            )
            if not (
                context.application.chat_data[
                    context.bot_data["data"]["agent_orders_group"]
                ].get(f"trusted_agent_orders_{serial}", False)
                and context.application.chat_data[
                    context.bot_data["data"]["partner_orders_group"]
                ].get(f"trusted_agent_orders_{serial}", False)
            ):
                pass

            else:
                team_cash_caption: str = context.application.chat_data[
                    context.bot_data["data"]["agent_orders_group"]
                ][f"trusted_agent_orders_{serial}"]

                promo_code_caption: str = context.application.chat_data[
                    context.bot_data["data"]["partner_orders_group"]
                ][f"trusted_agent_orders_{serial}"]

                await models.WorkWithUsOrder.approve_order(order_serial=serial)

                await context.bot.send_message(
                    chat_id=order.user_id,
                    text=(
                        f"مبروك، تمت الموافقة على طلبك للعمل معنا كوكيل لمحافظة <b>{syrian_govs_en_ar[order.gov]}</b>\n\n"
                        f"الرقم التسلسلي للطلب: <code>{serial}</code>\n\n"
                    ),
                )
                await context.bot.send_document(
                    chat_id=order.user_id,
                    document=os.getenv("TEAM_CASH_ID"),
                    caption="تطبيق شحن وسحب أرصدة اللاعبين:\n\n"
                    + "معلومات تسجيل الدخول:\n\n"
                    + team_cash_caption,
                )

                await context.bot.send_document(
                    chat_id=order.user_id,
                    document=os.getenv("PROMO_CODE_ID"),
                    caption="تطبيق استلام الأرباح من خسائر اللاعبين:\n\n"
                    + "معلومات تسجيل الدخول:\n\n"
                    + promo_code_caption,
                )

                await context.bot.send_message(
                    chat_id=order.user_id,
                    text=AGENT_COMMAND_TEXT,
                    reply_markup=build_agent_keyboard(),
                )
        else:
            await models.WorkWithUsOrder.approve_order(order_serial=serial)

            await context.bot.send_message(
                chat_id=order.user_id,
                text=(
                    f"مبروك، تمت الموافقة على طلبك للعمل معنا كشريك في محافظة <b>{syrian_govs_en_ar[order.gov]}</b>\n\n"
                    f"الرقم التسلسلي للطلب: <code>{serial}</code>\n\n"
                ),
            )
            await context.bot.send_document(
                chat_id=order.user_id,
                document=os.getenv("PROMO_CODE_ID"),
                caption="تطبيق استلام الأرباح من خسائر اللاعبين:\n\n"
                + "معلومات تسجيل الدخول:\n\n"
                + update.message.text_html,
            )

        await update.message.reply_to_message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تمت الموافقة ✅", callback_data="تمت الموافقة ✅"
                )
            )
        )


notify_agent_order_handler = CallbackQueryHandler(
    notify_w_with_us_order, "^notify_((agent)|(partner))_order_\d+$"
)
accept_agent_order_handler = CallbackQueryHandler(
    accept_w_with_us_order, "^accept_((agent)|(partner))_order_\d+$"
)

get_login_info_handler = MessageHandler(
    filters=AgentOrder()
    & ~Declined()
    & filters.REPLY
    & filters.TEXT
    & ~filters.COMMAND,
    callback=get_login_info,
)
