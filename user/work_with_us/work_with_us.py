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
    CallbackQueryHandler,
    MessageHandler,
    filters,
    CommandHandler,
)

from common.back_to_home_page import (
    back_to_user_home_page_button,
    back_to_user_home_page_handler,
)

from user.work_with_us.common import (
    work_with_us_keyboard,
    parent_to_child_mapper,
    WORK_WITH_US_DICT,
    build_govs_keyboard,
    govs_pattern,
    send_to_group,
)
from common.common import build_back_button, build_user_keyboard
from common.decorators import (
    check_user_call_on_or_off_decorator,
    check_if_user_present_decorator,
)
from common.back_to_home_page import (
    check_if_user_member_decorator,
    back_to_user_home_page_button,
)
from start import start_command
import models

(
    CHOOSE_WORKING_WITH_US,
    CHOOSE_WHAT_DO_U_WANNA_BE,
    CHOOSE_GOV,
    NEIGHBORHOOD,
    LOCATION,
    EMAIL,
    PHONE,
    FRONT_ID,
    BACK_ID,
    AMOUNT,
    REF_NUM,
    SCREEN_SHOT,
) = range(12)


@check_user_call_on_or_off_decorator
@check_if_user_present_decorator
@check_if_user_member_decorator
async def work_with_us(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await update.callback_query.edit_message_text(
            text="عملك معنا",
            reply_markup=InlineKeyboardMarkup(work_with_us_keyboard),
        )
        return CHOOSE_WORKING_WITH_US


async def choose_working_with_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not update.callback_query.data.startswith("back"):
            role = update.callback_query.data.split("_")[0]
            if role == "agent" and not update.effective_user.username:
                await update.callback_query.answer(
                    text="ليس لديك اسم مستخدم علي تيليجرام، يجب عليك اختيار اسم مستخدم لكي تتمكن من تقديم طلب وكيل.",
                    show_alert=True,
                )
                return
            context.user_data["work_with_us_role"] = role
        else:
            role = context.user_data["work_with_us_role"]
        choose_working_with_us_keyboard = [
            [WORK_WITH_US_DICT[role]["button"]],
            build_back_button("back_to_choose_working_with_us"),
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text=WORK_WITH_US_DICT[role]["text"],
            reply_markup=InlineKeyboardMarkup(choose_working_with_us_keyboard),
        )
        return CHOOSE_WHAT_DO_U_WANNA_BE


back_to_choose_working_with_us = work_with_us


async def choose_what_do_u_wanna_be(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        govs_keyboard = build_govs_keyboard()
        govs_keyboard.append(build_back_button("back_to_choose_what_do_u_wanna_be"))
        govs_keyboard.append(back_to_user_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر المحافظة التي ستعمل بها",
            reply_markup=InlineKeyboardMarkup(govs_keyboard),
        )
        return CHOOSE_GOV


back_to_choose_what_do_u_wanna_be = choose_working_with_us


async def choose_gov(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_choose_gov"),
            back_to_user_home_page_button[0],
        ]

        if update.callback_query:

            gov = update.callback_query.data.split("_")[0]
            worker = parent_to_child_mapper[
                context.user_data["work_with_us_role"]
            ].get_workers(
                gov=gov,
                user_id=update.effective_user.id,
            )

            if worker:
                await update.callback_query.answer(
                    text="أنت وكيل في هذه المحافظة بالفعل ❗️",
                    show_alert=True,
                )
                return

            context.user_data["w_with_us_gov"] = gov
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


back_to_choose_gov = choose_what_do_u_wanna_be


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
            context.user_data["w_with_us_neighborhood"] = update.message.text
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
            context.user_data["w_with_us_location"] = (
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
            context.user_data["w_with_us_email"] = update.message.text
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
            context.user_data["w_with_us_phone"] = update.message.text
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
            context.user_data["w_with_us_front_id"] = update.message.photo[-1]
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
            context.user_data["w_with_us_back_id"] = update.message.photo[-1]
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
            "<b>ملاحظة: التحويل مقبول فقط من أجهزة سيريتيل أو من خطوط الجملة الخاصة لمحلات الموبايل (غير مقبول التحويل من رقم شخصي)</b>"
        )
        if not update.callback_query:
            context.user_data["w_with_us_amount"] = float(update.message.text)
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


async def get_ref_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_get_amount"),
            back_to_user_home_page_button[0],
        ]
        if update.message:
            t_order = models.WorkWithUsOrder.get_one_order(ref_num=update.message.text)
            if t_order:
                await update.message.reply_text(
                    text="رقم عملية مكرر!",
                )
                return
            context.user_data["w_with_us_ref_num"] = update.message.text
            await update.message.reply_text(
                text="أخيراً، أرسل لقطة شاشة لعملية الدفع السابقة.",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text="أخيراً، أرسل لقطة شاشة لعملية الدفع السابقة.",
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )

        return SCREEN_SHOT


async def send_to_check_w_with_us_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE:
        serial = await models.WorkWithUsOrder.add_work_with_us_order(
            user_id=update.effective_user.id,
            gov=context.user_data["w_with_us_gov"],
            neighborhood=context.user_data["w_with_us_neighborhood"],
            latitude=context.user_data["w_with_us_location"][0],
            longitude=context.user_data["w_with_us_location"][1],
            email=context.user_data["w_with_us_email"],
            phone=context.user_data["w_with_us_phone"],
            amount=context.user_data["w_with_us_amount"],
            ref_num=context.user_data["w_with_us_ref_num"],
            role=context.user_data["work_with_us_role"],
        )
        photos = [
            update.message.photo[-1],
            context.user_data["w_with_us_back_id"],
            context.user_data["w_with_us_front_id"],
        ]

        await models.Photo.add(
            photos=photos,
            order_serial=serial,
            order_type=context.user_data["work_with_us_role"],
        )

        media = [InputMediaPhoto(media=p) for p in photos]

        await send_to_group(
            context=context,
            media=media,
            serial=serial,
            group_id=context.bot_data["data"]["partner_orders_group"],
        )
        if context.user_data["work_with_us_role"] == "agent":
            await send_to_group(
                context=context,
                media=media,
                serial=serial,
                group_id=context.bot_data["data"]["agent_orders_group"],
            )

        await update.message.reply_text(
            text="شكراً لك، تم إرسال طلبك للمراجعة، سيتم الرد عليك بأقرب وقت ممكن.",
            reply_markup=build_user_keyboard(),
        )
        return ConversationHandler.END


work_with_us_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            work_with_us,
            "^work with us$",
        ),
    ],
    states={
        CHOOSE_WORKING_WITH_US: [
            CallbackQueryHandler(
                choose_working_with_us,
                "^((agent)|(partner))_work_with_us$",
            ),
        ],
        CHOOSE_WHAT_DO_U_WANNA_BE: [
            CallbackQueryHandler(
                choose_what_do_u_wanna_be,
                "^wanna_be_((agent)|(partner))$",
            )
        ],
        CHOOSE_GOV: [
            CallbackQueryHandler(
                choose_gov,
                govs_pattern,
            )
        ],
        NEIGHBORHOOD: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_neighborhood,
            )
        ],
        LOCATION: [
            MessageHandler(
                filters=filters.LOCATION,
                callback=share_location,
            )
        ],
        EMAIL: [
            MessageHandler(
                filters=filters.Regex(r"^\S+@\S+\.\S+$"),
                callback=get_email,
            )
        ],
        PHONE: [
            MessageHandler(
                filters=filters.Regex("^\+\d+$"),
                callback=get_phone,
            )
        ],
        FRONT_ID: [
            MessageHandler(
                filters=filters.PHOTO,
                callback=get_front_id,
            )
        ],
        BACK_ID: [
            MessageHandler(
                filters=filters.PHOTO,
                callback=get_back_id,
            )
        ],
        AMOUNT: [
            MessageHandler(
                filters=filters.Regex("^\d+$"),
                callback=get_amount,
            )
        ],
        REF_NUM: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_ref_num,
            )
        ],
        SCREEN_SHOT: [
            MessageHandler(
                filters=filters.PHOTO,
                callback=send_to_check_w_with_us_order,
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_choose_what_do_u_wanna_be, "^back_to_choose_what_do_u_wanna_be$"
        ),
        CallbackQueryHandler(
            back_to_choose_working_with_us, "^back_to_choose_working_with_us$"
        ),
        CallbackQueryHandler(back_to_choose_gov, "^back_to_choose_gov$"),
        CommandHandler("back", back_to_get_neighborhood),
        CallbackQueryHandler(back_to_share_location, "^back_to_share_location$"),
        CallbackQueryHandler(back_to_get_email, "^back_to_get_email$"),
        CallbackQueryHandler(back_to_get_phone, "^back_to_get_phone$"),
        CallbackQueryHandler(back_to_get_front_id, "^back_to_get_front_id$"),
        CallbackQueryHandler(back_to_get_back_id, "^back_to_get_back_id$"),
        CallbackQueryHandler(back_to_get_amount, "^back_to_get_amount$"),
        start_command,
        back_to_user_home_page_handler,
    ],
    name="work_with_us_conversation",
    persistent=True,
)
