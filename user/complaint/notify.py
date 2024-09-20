from telegram import Update, Chat
from telegram.ext import ContextTypes, ConversationHandler
from common.common import build_user_keyboard, parent_to_child_models_mapper
from models import DepositOrder, WithdrawOrder, BuyUsdtdOrder
from PyroClientSingleton import PyroClientSingleton
import datetime


async def check_complaint_date(
    context: ContextTypes.DEFAULT_TYPE,
    serial: int,
    order_type: str,
):
    if not context.user_data.get(f"notified_{order_type}_orders", False):
        context.user_data[f"notified_{order_type}_orders"] = {
            serial: {
                "serial": serial,
                "date": datetime.datetime.now(),
            }
        }
        return True

    elif not context.user_data[f"notified_{order_type}_orders"].get(serial, False):
        context.user_data[f"notified_{order_type}_orders"][serial] = {
            "serial": serial,
            "date": datetime.datetime.now(),
        }
        return True

    date: datetime.datetime = context.user_data[f"notified_{order_type}_orders"][
        serial
    ]["date"]

    if (datetime.datetime.now() - date).days < 1:
        return False

    return True


def get_chat_id(
    order: DepositOrder | WithdrawOrder | BuyUsdtdOrder,
):
    group_id = (
        order.group_id
        if order.state in ["sent", "pending"]
        else order.worker_id if order.state == "processing" else order.checker_id
    )

    return group_id


def get_message_id(
    order: DepositOrder | WithdrawOrder | BuyUsdtdOrder,
):
    message_id = (
        order.processing_message_id
        if order.state == "processing"
        else (
            order.pending_process_message_id
            if order.state == "sent"
            else (
                order.checking_message_id
                if order.state == "checking"
                else order.pending_check_message_id
            )
        )
    )
    return message_id


async def send_notification(order_type: str, serial: int):
    order = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)
    cpyro = PyroClientSingleton()

    chat_id = get_chat_id(order)
    message_id = get_message_id(order)

    old_message = await cpyro.get_messages(
        chat_id=chat_id,
        message_ids=message_id,
    )
    message = await cpyro.copy_message(
        chat_id=chat_id,
        from_chat_id=chat_id,
        message_id=old_message.id,
        reply_markup=old_message.reply_markup,
    )

    await cpyro.send_message(
        chat_id=chat_id,
        text="وصلتنا شكوى تأخير بشأن الطلب أعلاه ⬆️",
    )
    await cpyro.delete_messages(
        chat_id=chat_id,
        message_ids=old_message.id,
    )

    message_id_fields = {
        "sent": "pending_process_message_id",
        "pending": "pending_check_message_id",
        "checking": "checking_message_id",
        "processing": "processing_message_id",
    }

    message_id_field = message_id_fields[order.state]
    if message_id_field:
        await parent_to_child_models_mapper[order_type].add_message_ids(
            serial=serial, **{message_id_field: message.id}
        )


async def notify_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        serial = int(update.callback_query.data.split("_")[-1])
        order_type = context.user_data["complaint_order_type"]
        res = await check_complaint_date(
            context=context,
            serial=serial,
            order_type=order_type,
        )

        if not res:
            await update.callback_query.answer(
                text="يمكنك إرسال تنبيه واحد عن كل طلب في اليوم ❗️",
                show_alert=True,
            )
            return

        try:
            await send_notification(order_type=order_type, serial=serial)
        except:
            pass

        context.user_data[
            f"notified_{context.user_data['complaint_order_type']}_orders"
        ][serial]["date"] = datetime.datetime.now()

        await update.callback_query.edit_message_text(
            text="شكراً لك، لقد تمت العملية بنجاح.",
            reply_markup=build_user_keyboard(),
        )

        return ConversationHandler.END
