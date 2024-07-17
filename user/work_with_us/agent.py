from telegram import (
    Update,
    InlineKeyboardMarkup,
    Chat,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InputMediaPhoto,
    ReplyKeyboardRemove,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)

from common.back_to_home_page import back_to_user_home_page_button
from user.work_with_us.common import send_to_group
from common.common import build_back_button, build_user_keyboard
from DB import DB
import asyncio

(
    NEIGHBORHOOD,
    LOCATION,
    EMAIL,
    PHONE,
    FRONT_ID,
    BACK_ID,
    AMOUNT,
    REF_NUM,
) = range(3, 11)


async def choose_gov(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        gov = update.callback_query.data.split("_")[0]
        agent = DB.get_trusted_agents(
            gov=gov,
            user_id=update.effective_user.id,
        )
        if agent:
            await update.callback_query.answer(
                text="أنت وكيل في هذه المحافظة بالفعل ❗️",
                show_alert=True,
            )
            return
        back_buttons = [
            build_back_button("back_to_choose_gov"),
            back_to_user_home_page_button[0],
        ]

        if update.callback_query:
            context.user_data["agent_gov"] = gov
            await update.callback_query.edit_message_text(
                text="جيد، الآن أرسل لنا اسم الحي الذي ستعمل فيه",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.message.reply_text(
                text="تم الرجوع",
                reply_markup=ReplyKeyboardRemove(),
            )

            await update.message.reply_text(
                text="جيد، الآن أرسل لنا اسم الحي الذي ستعمل فيه",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )

        return NEIGHBORHOOD


async def get_neighborhood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        text = (
            "قم بمشاركة موقعك معنا\n"
            "يمكنك الرجوع بالضغط على الأمر /back\n"
            "أو العودة إلى القائمة الرئيسية بالضغط على الأمر /start."
        )
        req_loc_button = ReplyKeyboardMarkup.from_button(
            KeyboardButton(text="شارك موقعك", request_location=True),
            resize_keyboard=True,
        )
        if not update.callback_query:
            context.user_data["agent_neighborhood"] = update.message.text
            await update.message.reply_text(
                text=text,
                reply_markup=req_loc_button,
            )
        else:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=req_loc_button,
            )

        return LOCATION


back_to_get_neighborhood = choose_gov


async def share_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_share_location"),
            back_to_user_home_page_button[0],
        ]
        if not update.callback_query:
            context.user_data["agent_location"] = (
                update.message.location.latitude,
                update.message.location.longitude,
            )
            await update.message.reply_text(
                text="تم استلام الموقع ✅",
                reply_markup=ReplyKeyboardRemove(),
            )
            await update.message.reply_text(
                text="أرسل الإيميل",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text="أرسل الإيميل",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )

        return EMAIL


back_to_share_location = get_neighborhood


async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_get_email"),
            back_to_user_home_page_button[0],
        ]
        if not update.callback_query:
            context.user_data["agent_email"] = update.message.text
            await update.message.reply_text(
                text="أرسل رقم الهاتف مسبوقاً بالرمز +",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text="أرسل رقم الهاتف مسبوقاً بالرمز +",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )

        return PHONE


back_to_get_email = share_location


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_get_phone"),
            back_to_user_home_page_button[0],
        ]
        if not update.callback_query:
            context.user_data["agent_phone"] = update.message.text
            await update.message.reply_text(
                text="أرسل صورة الوجه الأمامي لهويتك الشخصية",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text="أرسل صورة الوجه الأمامي لهويتك الشخصية",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )

        return FRONT_ID


back_to_get_phone = get_email


async def get_front_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_get_front_id"),
            back_to_user_home_page_button[0],
        ]
        if not update.callback_query:
            context.user_data["agent_front_id"] = update.message.photo[-1]
            await update.message.reply_text(
                text="جيد، الآن صورة الوجه الخلفي.",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text="جيد، الآن صورة الوجه الخلفي.",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )

        return BACK_ID


back_to_get_front_id = get_phone


async def get_back_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_get_back_id"),
            back_to_user_home_page_button[0],
        ]
        text = f"كم تريد الإيداع؟\n\n" "<b>ملاحظة: الحد الأدنى = 100 ألف ليرة</b>\n\n"
        if not update.callback_query:
            context.user_data["agent_back_id"] = update.message.photo[-1]
            await update.message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return AMOUNT


back_to_get_back_id = get_front_id


async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        amount = float(update.message.text)
        if amount < 100_000:
            await update.message.reply_text(
                "<b>ملاحظة: الحد الأدنى = 100 ألف ليرة</b>\n\n"
            )
            return
        back_buttons = [
            build_back_button("back_to_get_amount"),
            back_to_user_home_page_button[0],
        ]
        text = (
            f"أرسل مبلغ الإيداع المسبق إلى الرقم\n\n"
            f"<code>{context.bot_data['data']['طلبات الوكيل_number']}</code>\n\n"
            f"ثم أرسل رقم عملية الدفع إلى البوت لنقوم بتوثيقها.\n\n"
            "<b>ملاحظة: التحويل مقبول فقط من أجهزة سيريتيل أو من خطوط الجملة الخاصة لمحلات الموبايل .. 'غير مقبول التحويل من رقم شخصي'</b>"
        )
        if not update.callback_query:
            context.user_data["agent_amount"] = float(update.message.text)
            await update.message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return REF_NUM


back_to_get_amount = get_back_id


async def send_to_check_agent_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        t_order = DB.get_one_order("trusted_agents", ref_num=update.message.text)
        if t_order:
            await update.message.reply_text(
                text="رقم عملية مكرر!",
            )
            return
        serial = await DB.add_trusted_agent_order(
            user_id=update.effective_user.id,
            gov=context.user_data["agent_gov"],
            neighborhood=context.user_data["agent_neighborhood"],
            latitude=context.user_data["agent_location"][0],
            longitude=context.user_data["agent_location"][1],
            email=context.user_data["agent_email"],
            phone=context.user_data["agent_phone"],
            front_id=context.user_data["agent_front_id"],
            back_id=context.user_data["agent_back_id"],
            amount=context.user_data["agent_amount"],
            ref_num=update.message.text,
        )
        media = [
            InputMediaPhoto(
                media=context.user_data["agent_front_id"],
            ),
            InputMediaPhoto(
                media=context.user_data["agent_back_id"],
            ),
        ]

        await send_to_group(
            update=update,
            context=context,
            media=media,
            serial=serial,
            group_id=context.bot_data["data"]["agent_orders_group"],
        )
        await send_to_group(
            update=update,
            context=context,
            media=media,
            serial=serial,
            group_id=context.bot_data["data"]["partner_orders_group"],
        )

        await update.message.reply_text(
            text="شكراً لك، تم إرسال طلبك للمراجعة، سيتم الرد عليك بأقرب وقت ممكن.",
            reply_markup=build_user_keyboard(),
        )
        return ConversationHandler.END
