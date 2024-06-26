from telegram import (
    Update,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from custom_filters.User import User

from common.common import (
    build_user_keyboard,
    payment_method_pattern,
)

from common.force_join import (
    check_if_user_member_decorator
)
from common.back_to_home_page import (
    back_to_user_home_page_handler
)

from start import start_command

from DB import DB

(
    USDT_TO_BUY_AMOUNT,
    YES_NO_BUY_USDT,
    BUY_USDT_METHOD,
    BANK_NUMBER_BUY_USDT,
    CASH_CODE,
    BANK_ACCOUNT_NAME_BUY_USDT,
    BUY_USDT_CHECK,
) = range(7)

back_button = [
    [
        InlineKeyboardButton(
            text="العودة إلى القائمة الرئيسية🔝", callback_data="back to user home page"
        )
    ]
]

@check_if_user_member_decorator
async def buy_usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        if not context.bot_data["data"]["user_calls"]["buy_usdt"]:
            await update.callback_query.answer("شراء USDT متوقف حالياً❗️")
            return ConversationHandler.END

        user = DB.get_user(user_id=update.effective_user.id)
        if not user:
            new_user = update.effective_user
            await DB.add_new_user(
                user_id=new_user.id, username=new_user.username, name=new_user.full_name
            )

        text = f"""<b>1 USDT = {context.bot_data['data']['usdt_to_syp']} SYP</b>

كم تريد أن تبيع؟💵"""
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(back_button),
        )
        return USDT_TO_BUY_AMOUNT


async def usdt_to_buy_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        context.user_data["usdt_to_buy_amount"] = int(update.message.text)
        keyboard = [
            [
                InlineKeyboardButton(text="موافق👍", callback_data="yes buy usdt"),
                InlineKeyboardButton(text="غير موافق👎", callback_data="no buy usdt"),
            ],
            [
                InlineKeyboardButton(
                    text="الرجوع🔙", callback_data="back to usdt to buy amount"
                )
            ],
            back_button[0],
        ]
        text = f"""الكمية المرسلة تساوي:

<b>{context.user_data['usdt_to_buy_amount']} USDT = {int(context.user_data['usdt_to_buy_amount']) * context.bot_data['data']['usdt_to_syp']} SYP</b>

هل أنت موافق؟"""

        await update.message.reply_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return YES_NO_BUY_USDT


back_to_usdt_to_buy_amount = buy_usdt


async def yes_no_buy_usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        if update.callback_query.data.startswith("no"):
            await update.callback_query.answer("حسناً، تم الإلغاء")
            await update.callback_query.edit_message_text(
                text="القائمة الرئيسية🔝",
                reply_markup=build_user_keyboard(),
            )
            return ConversationHandler.END
        else:
            buy_usdt_methods = [
                [
                    InlineKeyboardButton(text="بيمو🇸🇦🇫🇷", callback_data="بيمو🇸🇦🇫🇷"),
                    InlineKeyboardButton(text="بركة🇧🇭", callback_data="بركة🇧🇭"),
                ],
                [
                    InlineKeyboardButton(
                        text="Syriatel Cash🇸🇾", callback_data="Syriatel Cash🇸🇾"
                    ),
                    InlineKeyboardButton(text="MTN Cash🇸🇾", callback_data="MTN Cash🇸🇾"),
                ],
            ]
            buy_usdt_methods.append(
                [
                    InlineKeyboardButton(
                        text="الرجوع🔙", callback_data="back to yes no buy usdt"
                    )
                ]
            )
            buy_usdt_methods.append(back_button[0])
            await update.callback_query.edit_message_text(
                text="اختر وسيلة الدفع لاستلام أموالك💳",
                reply_markup=InlineKeyboardMarkup(buy_usdt_methods),
            )
            return BUY_USDT_METHOD


async def back_to_yes_no_buy_usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        keyboard = [
            [
                InlineKeyboardButton(text="موافق👍", callback_data="yes buy usdt"),
                InlineKeyboardButton(text="غير موافق👎", callback_data="no buy usdt"),
            ],
            [
                InlineKeyboardButton(
                    text="الرجوع🔙", callback_data="back to buy usdt amount"
                )
            ],
            back_button[0],
        ]
        text = f"""الكمية المرسلة تساوي:

{context.user_data['usdt_to_buy_amount']} USDT = {int(context.user_data['usdt_to_buy_amount']) * context.bot_data['data']['usdt_to_syp']} SYP

هل أنت موافق؟"""

        await update.callback_query.edit_message_text(
            text=text, reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return YES_NO_BUY_USDT


async def buy_usdt_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):

        data = update.callback_query.data
        if not data.startswith("back"):
            method = DB.get_payment_method(name=data)

            if method[1] == 0:
                await update.callback_query.answer("هذه الوسيلة متوقفة مؤقتاً❗️")
                return

            context.user_data["payment_method_buy_usdt"] = data

        back_keyboard = [
            [
                InlineKeyboardButton(
                    text="الرجوع🔙", callback_data="back to buy usdt method"
                )
            ],
            back_button[0],
        ]

        if context.user_data["payment_method_buy_usdt"] in ["بيمو🇸🇦🇫🇷", "بركة🇧🇭"]:

            if context.user_data["payment_method_buy_usdt"] == "بيمو🇸🇦🇫🇷":
                text = "أرسل رقم حساب بيمو👝"
            else:
                text = "أرسل رقم حساب بركة👝"

            await update.callback_query.edit_message_text(
                text=text, reply_markup=InlineKeyboardMarkup(back_keyboard)
            )
            return BANK_NUMBER_BUY_USDT

        elif context.user_data["payment_method_buy_usdt"] == "Syriatel Cash🇸🇾":
            text = "أرسل رقم حساب سيريتيل كاش👝"

        elif context.user_data["payment_method_buy_usdt"] == "MTN Cash🇸🇾":
            text = "أرسل رقم حساب MTN كاش👝"

        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return CASH_CODE


async def back_to_cash_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        back_keyboard = [
            [
                InlineKeyboardButton(
                    text="الرجوع🔙", callback_data="back to buy usdt method"
                )
            ],
            back_button[0],
        ]
        if context.user_data["payment_method_buy_usdt"] == "Syriatel Cash🇸🇾":
            text = "أرسل رقم حساب سيريتيل كاش👝"

        elif context.user_data["payment_method_buy_usdt"] == "MTN Cash🇸🇾":
            text = "أرسل رقم حساب MTN كاش👝"

        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return CASH_CODE


async def back_to_bank_number_buy_usdt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        back_keyboard = [
            [
                InlineKeyboardButton(
                    text="الرجوع🔙", callback_data="back to payment method buy usdt"
                )
            ],
            back_button[0],
        ]
        name = (
            "بركة"
            if context.user_data["payment_method_buy_usdt"] == "بركة🇧🇭"
            else "بيمو"
        )
        await update.callback_query.edit_message_text(
            text=f"أرسل رقم حساب {name} 👝",
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return BANK_NUMBER_BUY_USDT


async def bank_number_buy_usdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        back_keyboard = [
            [
                InlineKeyboardButton(
                    text="الرجوع🔙", callback_data="back to bank number buy usdt"
                )
            ],
            back_button[0],
        ]
        context.user_data["payment_method_number_buy_usdt"] = update.message.text

        await update.message.reply_text(
            text="أرسل اسم صاحب الحساب كما هو مسجل بالبنك.",
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return BANK_ACCOUNT_NAME_BUY_USDT


async def back_to_bank_account_name_buy_usdt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        back_keyboard = [
            [
                InlineKeyboardButton(
                    text="الرجوع🔙", callback_data=f"back to bank number buy usdt"
                )
            ],
            back_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="أرسل اسم صاحب الحساب كما هو مسجل بالبنك.",
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return BANK_ACCOUNT_NAME_BUY_USDT


async def back_to_buy_usdt_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        buy_usdt_methods = [
            [
                InlineKeyboardButton(text="بيمو🇸🇦🇫🇷", callback_data="بيمو🇸🇦🇫🇷"),
                InlineKeyboardButton(text="بركة🇧🇭", callback_data="بركة🇧🇭"),
            ],
            [
                InlineKeyboardButton(
                    text="Syriatel Cash🇸🇾", callback_data="Syriatel Cash🇸🇾"
                ),
                InlineKeyboardButton(text="MTN Cash🇸🇾", callback_data="MTN Cash🇸🇾"),
            ],
        ]
        buy_usdt_methods.append(
            [
                InlineKeyboardButton(
                    text="الرجوع🔙", callback_data="back to yes no buy usdt"
                )
            ]
        )
        buy_usdt_methods.append(back_button[0])

        await update.callback_query.edit_message_text(
            text="اختر وسيلة الدفع لاستلام أموالك💳",
            reply_markup=InlineKeyboardMarkup(buy_usdt_methods),
        )
        return BUY_USDT_METHOD


async def cash_code_bank_account_name_buy_usdt(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):

        if context.user_data["payment_method_buy_usdt"] in (
            "Syriatel Cash🇸🇾",
            "MTN Cash🇸🇾",
        ):
            context.user_data["payment_method_number_buy_usdt"] = update.message.text
            context.user_data["bank_account_name_buy_usdt"] = ""

        else:
            context.user_data["bank_account_name_buy_usdt"] = update.message.text

        back_keyboard = [
            [
                InlineKeyboardButton(
                    text="الرجوع🔙",
                    callback_data=(
                        "back to cash code buy usdt"
                        if context.user_data["payment_method_buy_usdt"]
                        not in ["بيمو🇸🇦🇫🇷", "بركة🇧🇭"]
                        else "back to bank account name buy usdt"
                    ),
                )
            ],
            back_button[0],
        ]
        text = f"""أرسل الآن العملات إلى المحفظة:

<code>{context.bot_data['data']['USDT_number']}</code>

ثم أرسل لقطة شاشة لعملية الدفع إلى البوت لنقوم بتوثيقها.

<b>ملاحظة هامة: الشبكة المستخدمه هي TRC20</b>"""
        await update.message.reply_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )

        return BUY_USDT_CHECK


async def buy_usdt_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):

        method = context.user_data["payment_method_buy_usdt"]
        method_info = ""

        if method == "بيمو🇸🇦🇫🇷":
            method_info = f"""رقم حساب بيمو: <code>{context.user_data['payment_method_number_buy_usdt']}</code>
اسم صاحب الحساب: <code>{context.user_data['bank_account_name_buy_usdt']}</code>"""

        elif method == "بركة🇧🇭":
            method_info = f"""رقم حساب بركة: <code>{context.user_data['payment_method_number_buy_usdt']}</code>
اسم صاحب الحساب: <code>{context.user_data['bank_account_name_buy_usdt']}</code>"""

        elif method == "MTN Cash🇸🇾":
            method_info = f"""MTN Cash number: <code>{context.user_data['payment_method_number_buy_usdt']}</code>"""

        elif method == "Syriatel Cash🇸🇾":
            method_info = f"""Syriatel Cash number: <code>{context.user_data['payment_method_number_buy_usdt']}</code>"""

        serial = await DB.add_buy_usdt_order(
            group_id=context.bot_data["data"]["buy_usdt_orders_group"],
            user_id=update.effective_user.id,
            method=method,
            amount=context.user_data["usdt_to_buy_amount"],
            payment_method_number=context.user_data["payment_method_number_buy_usdt"],
            bank_account_name=context.user_data["bank_account_name_buy_usdt"],
        )

        user_info = f"""طلب شراء USDT جديد:

المبلغ💵: <code>{context.user_data['usdt_to_buy_amount']}</code> USDT
وسيلة الدفع💳: <b>{method}</b>

Serial: <code>{serial}</code>

{method_info}
"""

        callback_data_dict = {
            "name": "check buy usdt",
            "serial": serial,
            "user_id": update.effective_user.id,
            "amount": context.user_data["usdt_to_buy_amount"],
            "method": method,
            "payment_method_number": context.user_data[
                "payment_method_number_buy_usdt"
            ],
            "bank_account_name": context.user_data["bank_account_name_buy_usdt"],
        }

        check_button = [
            [InlineKeyboardButton(text="التحقق☑️", callback_data=callback_data_dict)],
        ]
        message = await context.bot.send_photo(
            chat_id=context.bot_data["data"]["buy_usdt_orders_group"],
            photo=update.message.photo[-1],
            caption=user_info,
            reply_markup=InlineKeyboardMarkup(check_button),
        )
        await DB.add_buy_usdt_pending_check_message_id(
            serial=serial, message_id=message.id
        )
        await update.message.reply_text(
            text="شكراً لك، تم إرسال طلبك إلى قسم المراجعة، سيصلك رد خلال وقت قصير.",
            reply_markup=build_user_keyboard(),
        )
        return ConversationHandler.END


buy_usdt_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(buy_usdt, "^buy usdt$")],
    states={
        USDT_TO_BUY_AMOUNT: [
            MessageHandler(
                filters=filters.Regex("^[1-9]+\.?\d*$"), callback=usdt_to_buy_amount
            )
        ],
        YES_NO_BUY_USDT: [
            CallbackQueryHandler(yes_no_buy_usdt, "^yes buy usdt$|^no buy usdt$")
        ],
        BUY_USDT_METHOD: [
            CallbackQueryHandler(buy_usdt_method, payment_method_pattern)
        ],
        BANK_NUMBER_BUY_USDT: [
            MessageHandler(
                filters=filters.Regex(".*") & ~filters.COMMAND,
                callback=bank_number_buy_usdt,
            )
        ],
        CASH_CODE: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=cash_code_bank_account_name_buy_usdt,
            )
        ],
        BANK_ACCOUNT_NAME_BUY_USDT: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=cash_code_bank_account_name_buy_usdt,
            )
        ],
        BUY_USDT_CHECK: [
            MessageHandler(filters=filters.PHOTO, callback=buy_usdt_check)
        ],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_buy_usdt_method, "^back to buy usdt method$"),
        CallbackQueryHandler(back_to_yes_no_buy_usdt, "^back to yes no buy usdt$"),
        CallbackQueryHandler(
            back_to_bank_number_buy_usdt, "^back to bank number buy usdt$"
        ),
        CallbackQueryHandler(
            back_to_bank_account_name_buy_usdt, "^back to bank account name buy usdt$"
        ),
        CallbackQueryHandler(back_to_cash_code, "^back to cash code buy usdt$"),
        CallbackQueryHandler(
            back_to_usdt_to_buy_amount, "^back to usdt to buy amount$"
        ),
        back_to_user_home_page_handler,
        start_command,
    ],
    name="buy_usdt_handler",
    persistent=True,
)
