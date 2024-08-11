from telegram import PhotoSize, InlineKeyboardButton, InlineKeyboardMarkup, Document
from telegram.ext import ContextTypes
from models import DepositOrder, DepositAgent
from common.common import notify_workers, send_to_media_archive
from common.stringifies import stringify_deposit_order
import asyncio

SEND_MONEY_TEXT = (
    "قم بإرسال المبلغ المراد إيداعه إلى:\n\n"
    "<code>{}</code>\n"
    "<code>{}</code>"
    "ثم أرسل لقطة شاشة أو ملف pdf لعملية الدفع إلى البوت لنقوم بتوثيقها.\n\n"
    "Send the money to:\n\n"
    "<code>{}</code>\n"
    "<code>{}</code>"
    "And send a screenshot or a pdf in order to confirm it."
)


async def send_to_check_deposit(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    amount: float,
    proof: PhotoSize | Document,
    method: str,
    acc_number: str,
    acc_from_bot:bool,
    target_group: int,
):
    serial = await DepositOrder.add_deposit_order(
        user_id=user_id,
        method=method,
        acc_number=acc_number,
        acc_from_bot=acc_from_bot,
        group_id=target_group,
        amount=amount,
        deposit_wallet=context.bot_data["data"][f"{method}_number"],
    )

    caption = stringify_deposit_order(
        amount=amount,
        account_number=acc_number,
        method=method,
        serial=serial,
        wal=context.bot_data["data"][f"{method}_number"],
        acc_from_bot=acc_from_bot,
    )
    markup = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(
            text="التحقق ☑️", callback_data=f"check_deposit_order_{serial}"
        )
    )
    if isinstance(proof, PhotoSize):
        message = await context.bot.send_photo(
            chat_id=target_group,
            photo=proof,
            caption=caption,
            reply_markup=markup,
        )
    else:
        message = await context.bot.send_document(
            chat_id=target_group,
            document=proof,
            caption=caption,
            reply_markup=markup,
        )

    await send_to_media_archive(
        context,
        media=proof,
        serial=serial,
        order_type="deposit",
    )

    await DepositOrder.add_message_ids(
        serial=serial, pending_check_message_id=message.id
    )

    workers = DepositAgent.get_workers()
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه يوجد طلب تحقق إيداع جديد 🚨",
        )
    )
