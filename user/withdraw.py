from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Chat,
)


from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from custom_filters.User import User

from common.common import (
    build_user_keyboard,
    build_methods_keyboard,
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
import asyncio

back_button = [
    [
        InlineKeyboardButton(
            text="العودة إلى القائمة الرئيسية🔝", callback_data="back to user home page"
        )
    ]
]

(
    AMOUNT,
    PAYMENT_METHOD,
    WALLET_CODE,
    BANK_NUMBER_WITHDRAW,
    MTN_CASH_NUMBER_WITHDRAW,
    SYR_CASH_NUMBER_WITHDRAW,
    BANK_ACCOUNT_NAME,
    ACCOUNT_NUMBER,
    PASSWORD,
    LAST_NAME,
) = range(10)

@check_if_user_member_decorator
async def withdraw_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):

        user = DB.get_user(user_id=update.effective_user.id)
        if not user:
            new_user = update.effective_user
            await DB.add_new_user(
                user_id=new_user.id, username=new_user.username, name=new_user.full_name
            )

        if not context.bot_data["data"]["user_calls"]["withdraw"]:
            await update.callback_query.answer("السحوبات متوقفة حالياً❗️")
            return ConversationHandler.END

        keyboard = [
            [
                InlineKeyboardButton(
                    text="سحب مكافآت🎁", callback_data="withdraw gifts"
                ),
                InlineKeyboardButton(
                    text="سحب رصيد👝", callback_data="withdraw balance"
                ),
            ],
            back_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="اختر ما الذي تريد سحبه❔", reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def withdraw_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        context.user_data["withdraw_type"] = update.callback_query.data
        back_buttons = [
            [
                InlineKeyboardButton(
                    text="الرجوع🔙", callback_data="back to withdraw section"
                )
            ],
            back_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="أرسل المبلغ المراد سحبه💵",
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return AMOUNT


async def back_to_withdraw_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        keyboard = [
            [
                InlineKeyboardButton(
                    text="سحب مكافآت🎁", callback_data="withdraw gifts"
                ),
                InlineKeyboardButton(
                    text="سحب رصيد👝", callback_data="withdraw balance"
                ),
            ],
            back_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="اختر ما الذي تريد سحبه❔", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END


async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        amount = float(update.message.text)
        context.user_data["withdrawal_amount"] = amount

        user = DB.get_user(user_id=update.effective_user.id)
        if (user[4] < amount or user[4] < 10_000) and context.user_data[
            "withdraw_type"
        ] == "withdraw gifts":
            text = f"""❌ عذراً يا عزيزي رصيد مكافآتك غير كافي لعملية السحب.

🎁 رصيد مكافآتك الحالي هو: <b>{user[4]}$</b>
Ⓜ️ الحد الأدنى للسحب: <b>10000$</b>
📤 المبلغ المراد سحبه: <b>{amount}$</b>"""
            await update.message.reply_text(
                text=text,
                reply_markup=build_user_keyboard(),
            )

            return ConversationHandler.END

        payment_methods = build_methods_keyboard()
        payment_methods.append(
            [
                InlineKeyboardButton(
                    text="الرجوع🔙", callback_data="back to withdraw type"
                )
            ]
        )
        payment_methods.append(back_button[0])

        await update.message.reply_text(
            text="اختر وسيلة الدفع💳",
            reply_markup=InlineKeyboardMarkup(payment_methods),
        )
        return PAYMENT_METHOD


back_to_withdraw_type = withdraw_type


async def payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):

        data = update.callback_query.data
        if not data.startswith("back"):
            method = DB.get_payment_method(name=data)
            if method[1] == 0:
                await update.callback_query.answer("هذه الوسيلة متوقفة مؤقتاً❗️")
                return

            context.user_data["payment_method"] = data

        back_keyboard = [
            [
                InlineKeyboardButton(
                    text="الرجوع🔙", callback_data="back to payment method"
                )
            ],
            back_button[0],
        ]

        if context.user_data["payment_method"] in ["بيمو🇸🇦🇫🇷", "بركة🇧🇭"]:

            if context.user_data["payment_method"] == "بيمو🇸🇦🇫🇷":
                text = "أرسل رقم حساب بيمو👝"
            else:
                text = "أرسل رقم حساب بركة👝"

            await update.callback_query.edit_message_text(
                text=text, reply_markup=InlineKeyboardMarkup(back_keyboard)
            )
            return BANK_NUMBER_WITHDRAW

        elif context.user_data["payment_method"] == "USDT":
            text = "أرسل كود محفظتك👝\n\n<b>ملاحظة هامة: الشبكة المستخدمه هي TRC20</b>"

        elif context.user_data["payment_method"] == "Syriatel Cash🇸🇾":
            text = "أرسل رقم حساب سيريتيل كاش👝"

        elif context.user_data["payment_method"] == "MTN Cash🇸🇾":
            text = "أرسل رقم حساب MTN كاش👝"

        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return WALLET_CODE


async def back_to_withdraw_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        back_buttons = [
            [
                InlineKeyboardButton(
                    text="الرجوع🔙", callback_data="back to withdraw type"
                )
            ],
            back_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="أرسل المبلغ المراد سحبه💵",
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return AMOUNT


async def bank_number_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        back_keyboard = [
            [
                InlineKeyboardButton(
                    text="الرجوع🔙", callback_data="back to bank number withdraw"
                )
            ],
            back_button[0],
        ]
        context.user_data["payment_method_number"] = update.message.text

        await update.message.reply_text(
            text="أرسل اسم صاحب الحساب كما هو مسجل بالبنك.",
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return BANK_ACCOUNT_NAME


async def back_to_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        payment_methods = build_methods_keyboard()
        payment_methods.append(
            [
                InlineKeyboardButton(
                    text="الرجوع🔙", callback_data="back to withdraw type"
                )
            ]
        )
        payment_methods.append(back_button[0])

        await update.callback_query.edit_message_text(
            text="اختر وسيلة الدفع💳",
            reply_markup=InlineKeyboardMarkup(payment_methods),
        )
        return PAYMENT_METHOD


async def wallet_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        if context.user_data["payment_method"] in (
            "USDT",
            "Syriatel Cash🇸🇾",
            "MTN Cash🇸🇾",
        ):
            context.user_data["payment_method_number"] = update.message.text
            context.user_data["bank_account_name"] = ""
        else:
            context.user_data["bank_account_name"] = update.message.text

        back_keyboard = [
            [
                InlineKeyboardButton(
                    text="الرجوع🔙",
                    callback_data=(
                        "back to payment method"
                        if context.user_data["payment_method"]
                        not in ["بيمو🇸🇦🇫🇷", "بركة🇧🇭"]
                        else "back to bank account name"
                    ),
                )
            ],
            back_button[0],
        ]
        await update.message.reply_text(
            text="أرسل رقم حسابك🔢", reply_markup=InlineKeyboardMarkup(back_keyboard)
        )
        return ACCOUNT_NUMBER


async def back_to_bank_number_withdraw(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        back_keyboard = [
            [
                InlineKeyboardButton(
                    text="الرجوع🔙", callback_data="back to payment method"
                )
            ],
            back_button[0],
        ]
        name = "بركة" if context.user_data["payment_method"] == "بركة🇧🇭" else "بيمو"
        await update.callback_query.edit_message_text(
            text=f"أرسل رقم حساب {name} 👝",
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return BANK_NUMBER_WITHDRAW


bank_account_name = wallet_code


async def back_to_bank_account_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        back_keyboard = [
            [
                InlineKeyboardButton(
                    text="الرجوع🔙", callback_data=f"back to bank number withdraw"
                )
            ],
            back_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="أرسل اسم صاحب الحساب كما هو مسجل بالبنك.",
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return BANK_ACCOUNT_NAME


back_to_payment_info = payment_method


async def account_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        context.user_data["account_number"] = update.message.text

        back_keyboard = [
            [
                InlineKeyboardButton(
                    text="الرجوع🔙", callback_data="back to account number"
                )
            ],
            back_button[0],
        ]
        await update.message.reply_text(
            text="أرسل كلمة مرور حسابك🈴",
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return PASSWORD


async def back_to_account_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        back_keyboard = [
            [
                InlineKeyboardButton(
                    text="الرجوع🔙", callback_data="back to payment info"
                )
            ],
            back_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="أرسل رقم حسابك🔢", reply_markup=InlineKeyboardMarkup(back_keyboard)
        )
        return ACCOUNT_NUMBER


async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        context.user_data["password"] = update.message.text
        back_keyboard = [
            [InlineKeyboardButton(text="الرجوع🔙", callback_data="back to password")],
            back_button[0],
        ]
        await update.message.reply_text(
            text="أرسل الكنية/العائلة🔤",
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return LAST_NAME


async def back_to_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        back_keyboard = [
            [
                InlineKeyboardButton(
                    text="الرجوع🔙", callback_data="back to account number"
                )
            ],
            back_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="أرسل كلمة مرور حسابك🈴",
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return PASSWORD


async def get_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):

        amount = context.user_data["withdrawal_amount"]

        if context.user_data["withdraw_type"] == "withdraw gifts":
            await DB.update_gifts_balance(
                user_id=update.effective_user.id, amount=-amount
            )

        method = context.user_data["payment_method"]

        method_info = ""
        if method == "USDT":
            method_info = f"<b>USDT(TRC20) wallet code</b>: <code>{context.user_data['payment_method_number']}</code>"

        elif method == "MTN Cash🇸🇾":
            method_info = f"""MTN Cash number: <code>{context.user_data['payment_method_number']}</code>"""

        elif method == "Syriatel Cash🇸🇾":
            method_info = f"""Syriatel Cash number: <code>{context.user_data['payment_method_number']}</code>"""

        elif method == "بيمو🇸🇦🇫🇷":
            method_info = f"""رقم حساب بيمو: <code>{context.user_data['payment_method_number']}</code>
اسم صاحب الحساب: <b>{context.user_data['bank_account_name']}</b>"""

        elif method == "بركة🇧🇭":
            method_info = f"""رقم حساب بركة: <code>{context.user_data['payment_method_number']}</code>
اسم صاحب الحساب: <b>{context.user_data['bank_account_name']}</b>"""

        serial = await DB.add_withdraw_order(
            group_id=context.bot_data["data"]["withdraw_orders_group"],
            user_id=update.effective_user.id,
            method=method,
            acc_number=context.user_data["account_number"],
            password=context.user_data["password"],
            last_name=update.message.text,
            amount=amount,
            bank_account_name=context.user_data["bank_account_name"],
            payment_method_number=context.user_data["payment_method_number"],
        )

        user_info = f"""تفاصيل طلب سحب {'مكافأة' if context.user_data['withdraw_type'] == 'withdraw gifts' else ''}:

رقم حسابه🔢: <code>{context.user_data['account_number']}</code>
كلمة المرور🈴: <code>{context.user_data['password']}</code>
الكنية: <code>{update.message.text}</code>

المبلغ💵: <code>{amount}</code>
وسيلة الدفع💳: <b>{method}</b>

Serial: <code>{serial}</code>

{method_info}

تحقق من توفر المبلغ وقم بقبول/رفض الطلب بناء على ذلك.
"""

        check_withdraw_callback_data = {
            "name": "check withdraw",
            "serial": serial,
            "amount": amount,
            "method": method,
            "acc_number": context.user_data["account_number"],
            "password": context.user_data["password"],
            "user_id": update.effective_user.id,
            "last_name": update.message.text,
            "payment_method_number": context.user_data["payment_method_number"],
            "bank_account_name": context.user_data["bank_account_name"],
        }

        check_button = [
            [
                InlineKeyboardButton(
                    text="التحقق☑️", callback_data=check_withdraw_callback_data
                )
            ],
        ]
        message = await context.bot.send_message(
            chat_id=context.bot_data["data"]["withdraw_orders_group"],
            text=user_info,
            reply_markup=InlineKeyboardMarkup(check_button),
        )

        await DB.add_withdraw_pending_check_message_id(
            serial=serial, message_id=message.id
        )

        await update.message.reply_text(
            text="شكراً لك، تم إرسال طلبك إلى قسم المراجعة، سيصلك رد خلال وقت قصير.",
            reply_markup=build_user_keyboard(),
        )

        return ConversationHandler.END


withdraw_section_handler = CallbackQueryHandler(withdraw_section, "^withdraw$")

withdraw_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(withdraw_type, "^withdraw gifts$|^withdraw balance$")
    ],
    states={
        PAYMENT_METHOD: [CallbackQueryHandler(payment_method, payment_method_pattern)],
        WALLET_CODE: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND, callback=wallet_code
            )
        ],
        BANK_ACCOUNT_NAME: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND, callback=bank_account_name
            )
        ],
        BANK_NUMBER_WITHDRAW: [
            MessageHandler(
                filters=filters.Regex(".*") & ~filters.COMMAND,
                callback=bank_number_withdraw,
            )
        ],  # TODO add a regex
        AMOUNT: [
            MessageHandler(
                filters=filters.Regex("^[1-9]+\.?\d*$") & ~filters.COMMAND,
                callback=get_amount,
            )
        ],
        ACCOUNT_NUMBER: [
            MessageHandler(
                filters=filters.Regex(".*") & ~filters.COMMAND, callback=account_number
            )
        ],  # TODO add a regex
        PASSWORD: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND, callback=get_password
            )
        ],
        LAST_NAME: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND, callback=get_last_name
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_payment_method, "^back to payment method$"),
        CallbackQueryHandler(back_to_withdraw_amount, "^back to withdraw amount$"),
        CallbackQueryHandler(back_to_bank_account_name, "^back to bank account name$"),
        CallbackQueryHandler(
            back_to_bank_number_withdraw, "^back to bank number withdraw$"
        ),
        CallbackQueryHandler(back_to_withdraw_section, "^back to withdraw section$"),
        CallbackQueryHandler(back_to_password, "^back to password$"),
        CallbackQueryHandler(back_to_account_number, "^back to account number$"),
        CallbackQueryHandler(back_to_payment_info, "^back to peyment info$"),
        CallbackQueryHandler(back_to_withdraw_type, "^back to withdraw type$"),
        back_to_user_home_page_handler,
        start_command,
    ],
    name="withdraw_handler",
    persistent=True,
)
