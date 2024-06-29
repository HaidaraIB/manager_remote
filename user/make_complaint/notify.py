from telegram import (
    Update,
    Chat,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)


from common.common import (
    build_user_keyboard,
)

from PyroClientSingleton import PyroClientSingleton
from DB import DB
import datetime


async def check_complaint_date(
    context: ContextTypes.DEFAULT_TYPE,
    serial: int,
    order_type: str,
):
    if not context.user_data.get(f"notified_{order_type}_operations", False):
        context.user_data[f"notified_{order_type}_operations"] = {
            serial: {
                "serial": serial,
                "date": datetime.datetime.now(),
            }
        }
        return True

    elif not context.user_data[f"notified_{order_type}_operations"].get(serial, False):
        context.user_data[f"notified_{order_type}_operations"][serial] = {
            "serial": serial,
            "date": datetime.datetime.now(),
        }
        return True

    date: datetime.datetime = context.user_data[f"notified_{order_type}_operations"][
        serial
    ]["date"]

    if (datetime.datetime.now() - date).days < 1:

        return False

    return True


async def notify_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        serial = int(update.callback_query.data.split("_")[-1])

        op = DB.get_one_order(
            order_type=context.user_data["complaint_about"],
            serial=serial,
        )
        res = await check_complaint_date(
            context=context,
            serial=serial,
            order_type=context.user_data["complaint_about"],
        )

        if not res:
            await update.callback_query.answer(
                "يمكنك إرسال تنبيه واحد عن كل طلب في اليوم❗️"
            )
            return

        cpyro = PyroClientSingleton()
        try:
            await cpyro.start()
        except ConnectionError:
            pass

        old_message = await cpyro.get_messages(
            chat_id=op["worker_id"] if op["working_on_it"] else op["group_id"],
            message_ids=(
                op["pending_process_message_id"]
                if op["pending_process_message_id"]
                else op["pending_check_message_id"]
            ),
        )
        message = await cpyro.copy_message(
            chat_id=op["worker_id"] if op["working_on_it"] else op["group_id"],
            from_chat_id=(op["worker_id"] if op["working_on_it"] else op["group_id"]),
            message_id=(
                op["pending_process_message_id"]
                if op["pending_process_message_id"]
                else op["pending_check_message_id"]
            ),
            reply_markup=old_message.reply_markup,
        )

        await cpyro.send_message(
            chat_id=op["worker_id"] if op["working_on_it"] else op["group_id"],
            text="وصلتنا شكوى تأخير بشأن الطلب أعلاه⬆️",
        )
        await cpyro.delete_messages(
            chat_id=op["worker_id"] if op["working_on_it"] else op["group_id"],
            message_ids=(
                op["pending_process_message_id"]
                if op["pending_process_message_id"]
                else op["pending_check_message_id"]
            ),
        )


        if op["state"] == "sent":
            if op["working_on_it"]:
                await DB.add_message_ids(
                    order_type=context.user_data["complaint_about"],
                    serial=serial,
                    processing_message_id=message.id,
                )
            else:
                await DB.add_message_ids(
                    order_type=context.user_data["complaint_about"],
                    serial=serial,
                    pending_process_message_id=message.id,
                )
        else:
            if op["working_on_it"]:
                await DB.add_message_ids(
                    order_type=context.user_data["complaint_about"],
                    serial=serial,
                    checking_message_id=message.id,
                )
            else:
                await DB.add_message_ids(
                    order_type=context.user_data["complaint_about"],
                    serial=serial,
                    pending_check_message_id=message.id,
                )

        context.user_data[
            f"notified_{context.user_data['complaint_about']}_operations"
        ][serial]["date"] = datetime.datetime.now()

        await update.callback_query.edit_message_text(
            text="شكراً لك، لقد تمت العملية بنجاح.",
            reply_markup=build_user_keyboard(),
        )

        return ConversationHandler.END
