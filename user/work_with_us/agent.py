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
from user.work_with_us.common import stringify_agent_order
from common.common import build_back_button, build_user_keyboard
import os
from DB import DB

(
    FRONT_ID,
    BACK_ID,
    PRE_BALANCE,
    GOV,
    WITHDRAW_NAME,
    LOCATION,
) = range(3, 9)


async def get_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_get_full_name"),
            back_to_user_home_page_button[0],
        ]
        if not update.callback_query:
            context.user_data["work_with_us_full_name"] = update.message.text
            await update.message.reply_text(
                text="جيد، الآن أرسل لنا صورة الوجه الأمامي لهويتك الشخصية.",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text="جيد، الآن أرسل لنا صورة الوجه الأمامي لهويتك الشخصية.",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )

        return FRONT_ID


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


back_to_get_front_id = get_full_name


async def get_back_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_get_back_id"),
            back_to_user_home_page_button[0],
        ]
        if not update.callback_query:
            context.user_data["agent_back_id"] = update.message.photo[-1]
            await update.message.reply_text(
                text="أرسل الآن مبلغ الإيداع المسبق.",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text="أرسل الآن مبلغ الإيداع المسبق.",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return PRE_BALANCE


back_to_get_back_id = get_front_id


async def get_pre_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_get_pre_balance"),
            back_to_user_home_page_button[0],
        ]
        if not update.callback_query:
            context.user_data["agent_pre_balance"] = float(update.message.text)
            await update.message.reply_text(
                text="أرسل المحافظة التي ستعمل بها",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text="أرسل المحافظة التي ستعمل بها",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )

        return GOV


back_to_get_pre_balance = get_back_id


async def get_gov(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_get_gov"),
            back_to_user_home_page_button[0],
        ]
        if not update.message.text == '/back':
            context.user_data["agent_gov"] = update.message.text
        else:
            await update.message.reply_text(
                text="تم الرجوع",
                reply_markup=ReplyKeyboardRemove(),
            )
        await update.message.reply_text(
            text="أرسل الاسم الذي ترغب بالظهور به للمستخدمين أثناء السحب 'انجليزي'",
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return WITHDRAW_NAME


back_to_get_gov = get_pre_balance


async def get_withdraw_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        context.user_data["agent_withdraw_name"] = update.message.text
        await update.message.reply_text(
            text=(
                "أخيراً، قم بمشاركة موقعك معنا\n"
                "يمكنك الرجوع بالضغط على الأمر /back\n"
                "أو العودة إلى القائمة الرئيسية بالضغط على الأمر /start."
            ),
            reply_markup=ReplyKeyboardMarkup.from_button(
                KeyboardButton(text="شارك موقعك", request_location=True),
                resize_keyboard=True,
            ),
        )
        return LOCATION

back_to_get_withdraw_name = get_gov

async def share_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await DB.add_work_with_us_order(
            user_id=update.effective_user.id,
            full_name=context.user_data["agent_full_name"],
            back_id=context.user_data["agent_back_id"],
            front_id=context.user_data["agent_front_id"],
            gov=context.user_data["agent_gov"],
            latitude=update.message.location.latitude,
            longitude=update.message.location.longitude,
            pre_balance=context.user_data["agent_pre_balance"],
            withdraw_name=context.user_data["agent_withdraw_name"],
        )
        media = [
            InputMediaPhoto(
                media=context.user_data["agent_front_id"],
            ),
            InputMediaPhoto(
                media=context.user_data["agent_back_id"],
            ),
        ]
        await context.bot.send_media_group(
            chat_id=int(os.getenv("OWNER_ID")),
            media=media,
            caption=stringify_agent_order(
                full_name=context.user_data["agent_full_name"],
                gov=context.user_data["agent_gov"],
                pre_balance=context.user_data["agent_pre_balance"],
                withdraw_name=context.user_data["agent_withdraw_name"],
            ),
        )
        await context.bot.send_location(
            chat_id=int(os.getenv("OWNER_ID")),
            longitude=update.message.location.longitude,
            latitude=update.message.location.latitude,
        )
        await update.message.reply_text(
            text="شكراً لك، تم إرسال طلبك للمراجعة، سيتم الرد عليك بأقرب وقت ممكن.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await update.message.reply_text(
            text="القائمة الرئيسية🔝",
            reply_markup=build_user_keyboard(),
        )
        return ConversationHandler.END
