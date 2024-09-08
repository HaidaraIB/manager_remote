from telegram import Update, Chat
from telegram.ext import ContextTypes, CallbackQueryHandler

from custom_filters import Admin

from common.constants import *
from common.common import parent_to_child_models_mapper
from worker.request_order.common import get_order_message


from admin.order_settings.common import refresh_order_settings_message


async def return_order_to_worker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        data = update.callback_query.data.split("_")
        serial = int(data[-1])
        order_type = data[-3]
        order = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)
        if order.state == "approved":
            message = await get_order_message(
                group_id=order.group_id,
                message_id=order.pending_process_message_id,
                worker_id=order.worker_id,
            )
            if order_type in ["withdraw", "busdt"]:
                await parent_to_child_models_mapper[order_type].unapprove_payment_order(
                    serial=serial,
                    amount=order.amount,
                    method=order.method,
                    worker_id=order.worker_id,
                )
            else:
                await parent_to_child_models_mapper[order_type].unapprove_deposit_order(
                    serial=serial,
                    worker_id=order.worker_id,
                    amount=order.amount,
                    user_id=order.user_id,
                )
            await parent_to_child_models_mapper[order_type].add_message_ids(
                serial=serial,
                processing_message_id=message.id,
            )
        else:
            if order_type == "deposit":
                await update.callback_query.answer(
                    text="البوت هو من يقوم بمهام تحقق الإيداع ❗️",
                    show_alert=True,
                )
                return
            message = await get_order_message(
                group_id=order.group_id,
                message_id=order.pending_check_message_id,
                worker_id=order.checker_id,
            )
            if order.state == "declined":
                await parent_to_child_models_mapper[order_type].undecline_order(
                    serial=serial
                )
            elif order.state == "sent":
                await parent_to_child_models_mapper[order_type].unsend_order(
                    serial=serial,
                    group_id=context.bot_data["data"][f"{order_type}_orders_group"],
                )
            await parent_to_child_models_mapper[order_type].add_message_ids(
                serial=serial,
                checking_message_id=message.id,
            )

        await context.bot.send_message(
            chat_id=order.worker_id,
            text="تمت إعادة الطلب أعلاه من قبل الإدارة ⬆️⬆️⬆️",
        )
        await update.callback_query.delete_message()
        await refresh_order_settings_message(
            update=update,
            context=context,
            serial=serial,
            order_type=order_type,
            note="\n\nتمت إعادة الطلب إلى الموظف المسؤول ✅",
        )


return_order_to_worker_handler = CallbackQueryHandler(
    return_order_to_worker, "admin_return_((deposit)|(withdraw)|(busdt))_order"
)
