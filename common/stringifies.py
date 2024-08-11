import models
from common.common import format_amount, format_datetime, parent_to_child_models_mapper
from common.constants import *

state_dict_en_to_ar = {
    "declined": "مرفوض",
    "approved": "تمت الموافقة",
    "returned": "طلب معاد",
    "pending": "بانتظار التحقق",
    "sent": "بانتظار التنفيذ",
}

worker_type_dict = {
    "daily": {
        "approved_work": "approved_withdraws_day",
        "percentage": "workers_reward_withdraw_percentage",
        "role": "withdraws",
        "day_week": {
            "ar": "اليوم",
            "en": "day",
        },
        "model": models.PaymentAgent,
    },
    "weekly": {
        "approved_work": "approved_deposits_week",
        "percentage": "workers_reward_percentage",
        "role": "deposits",
        "day_week": {"ar": "الأسبوع", "en": "week"},
        "model": models.DepositAgent,
    },
}


def stringify_manager_reward_report(
    worker: models.DepositAgent | models.PaymentAgent,
    updated_worker: models.DepositAgent | models.PaymentAgent,
    amount: float,
    reward_type: str,
):
    manager_text = (
        f"تم تحديث رصيد المكافآت عن مجموع مبالغ الطلبات الناجحة للموظف:\n\n"
        f"id: <code>{worker.id}</code>\n"
        f"name: <b>{worker.name}</b>\n"
        f"username: {'@' + worker.username if worker.username else '<b>لا يوجد</b>'}\n\n"
    )
    return manager_text + stringify_reward_report(
        worker=worker,
        updated_worker=updated_worker,
        amount=amount,
        reward_type=reward_type,
    )


def stringify_reward_report(
    worker: models.DepositAgent | models.PaymentAgent,
    updated_worker: models.DepositAgent | models.PaymentAgent,
    amount: float,
    reward_type: str,
):
    role = worker_type_dict[reward_type]["role"]
    balance = updated_worker.__getattribute__(f"approved_{role}")
    partial_balance = worker.__getattribute__(
        f"approved_{role}_{worker_type_dict[reward_type]['day_week']['en']}"
    )
    prev_rewards_balance = worker.__getattribute__(f"{reward_type}_rewards_balance")
    rewards_balance = updated_worker.__getattribute__(f"{reward_type}_rewards_balance")
    orders_num = updated_worker.__getattribute__(f"approved_{role}_num")
    work_type = worker_type_dict[reward_type]["day_week"]["ar"]

    worker_text = (
        f"الوظيفة: {f'سحب {updated_worker.method}' if role == 'withdraws' else 'تنفيذ إيداع'}\n"
        f"مجموع المكافآت السابق: <b>{format_amount(prev_rewards_balance)}</b>\n"
        f"قيمة المكافأة: <b>{format_amount(amount)}</b>\n"
        f"مجموع المكافآت الحالي: <b>{format_amount(rewards_balance)}</b>\n"
        f"عدد الطلبات حتى الآن: <b>{orders_num}</b>\n"
        f"مجموع المبالغ حتى الآن: <b>{format_amount(balance)}</b>\n"
        f"مجموع المبالغ هذا {work_type}: <b>{format_amount(partial_balance)}</b>\n"
    )
    worker_text += (
        f"الدفعات المسبقة:\n{format_amount(worker.pre_balance)}\n"
        if isinstance(worker, models.PaymentAgent)
        else ""
    )

    return worker_text


order_settings_dict: dict[
    str, dict[str, models.WithdrawOrder | models.DepositOrder | models.BuyUsdtdOrder]
] = {
    "withdraw": {"cls": models.WithdrawOrder, "t": "سحب"},
    "deposit": {"cls": models.DepositOrder, "t": "إيداع"},
    "busdt": {"cls": models.BuyUsdtdOrder, "t": "شراء USDT"},
}


def general_stringify_order(serial: int, order_type: str, name: str):
    order = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)
    return (
        f"تفاصيل الطلب:\n\n"
        f"الرقم التسلسلي: <code>{order.serial}</code>\n\n"
        f"آيدي المستخدم صاحب الطلب: <code>{order.user_id}</code>\n"
        f"اسمه: <b>{name}</b>\n\n"
        f"نوع الطلب: <b>{order_settings_dict[order_type]['t']}</b>\n"
        f"المبلغ: <code>{format_amount(order.amount)}</code>\n"
        f"رقم الحساب: <code>{getattr(order, 'acc_number', 'لا يوجد')}</code>\n"
        f"حساب منشأ من البوت: <code>{'نعم' if getattr(order,'acc_from_bot', 'ليس طلب إيداع') else 'لا'}</code>\n\n"
        f"وسيلة الدفع: <code>{order.method}</code>\n"
        f"محفظة الإيداع: <code>{getattr(order, 'deposit_wallet', 'لا يوجد')}</code>\n\n"
        f"الحالة: <b>{state_dict_en_to_ar[order.state]}</b>\n"
        f"سبب إعادة/رفض: <b>{'\n' + order.reason if order.reason else 'لا يوجد'}</b>\n\n"
        f"جاري العمل عليه: <b>{'نعم' if order.working_on_it else 'لا'}</b>\n"
        f"تم إغلاق شكوى عنه : <b>{'نعم' if order.complaint_took_care_of else 'لا'}</b>\n\n"
        f"تاريخ الإنشاء:\n<b>{format_datetime(order.order_date)}</b>\n\n"
        f"تاريخ الإرسال: <b>{'\n' + format_datetime(order.send_date) if order.send_date else 'لا يوجد'}</b>\n\n"
        f"تاريخ الموافقة: <b>{'\n' + format_datetime(order.approve_date) if order.approve_date else 'لا يوجد'}</b>\n\n"
        f"تاريخ الرفض: <b>{'\n' + format_datetime(order.decline_date) if order.decline_date else 'لا يوجد'}</b>\n\n"
        f"تاريخ الإعادة: <b>{'\n' + format_datetime(order.return_date) if order.return_date else 'لا يوجد'}</b>\n\n"
    )


def complaint_stringify_order(serial: int, order_type: str):
    op = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)
    return (
        f"الرقم التسلسلي: <code>{op.serial}</code>\n"
        f"المبلغ: <b>{format_amount(op.amount)}</b>\n"
        f"وسيلة الدفع: <b>{op.method}</b>\n"
        f"عنوان الدفع: <code>{getattr(op, 'payment_method_number', NONE_TEXT)}</code>\n"
        f"اسم صاحب الحساب البنكي: <code>{getattr(op, 'bank_account_name', NONE_TEXT)}</code>\n"
        f"الحالة: <b>{state_dict_en_to_ar[op.state]}</b>\n"
        f"سبب إعادة/رفض: <b>{op.reason if op.reason else NONE_TEXT}</b>\n\n"
        f"Serial: <code>{op.serial}</code>\n"
        f"Amount: <b>{format_amount(op.amount)}</b>\n"
        f"Payment Method: <b>{op.method}</b>\n"
        f"Payment Info: <code>{getattr(op, 'payment_method_number', NONE_TEXT)}</code>\n"
        f"Bank Account Name: <code>{getattr(op, 'bank_account_name', NONE_TEXT)}</code>\n"
        f"State: <b>{state_dict_en_to_ar[op.state]}</b>\n"
        f"Decline/Return Reason: <b>{op.reason if op.reason else NONE_TEXT}</b>\n\n"
    )


def stringify_deposit_order(
    amount: float,
    serial: int,
    method: str,
    account_number: int,
    wal: str,
    acc_from_bot: bool,
    *args,
):
    return (
        "إيداع جديد:\n"
        f"المبلغ 💵: <code>{amount if amount else 'لا يوجد بعد'}</code>\n"
        f"رقم الحساب: <code>{account_number}</code>\n"
        f"حساب منشأ من البوت: <code>{'نعم' if acc_from_bot else 'لا'}</code>\n\n"
        f"وسيلة الدفع: <code>{method}</code>\n"
        f"المحفظة: <code>{wal}</code>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        "تنبيه: اضغط على رقم الحساب والمبلغ لنسخها كما هي في الرسالة تفادياً للخطأ."
    )


def stringify_check_withdraw_order(
    w_type: str,
    acc_number: int,
    password: str,
    withdraw_code: str,
    method: str,
    serial: int,
    method_info: str,
):
    g_b_dict = {"gift": "مكافأة", "balance": "رصيد"}
    return (
        f"تفاصيل طلب سحب {g_b_dict[w_type]}:\n\n"
        f"رقم الحساب 🔢: <code>{acc_number}</code>\n"
        f"كلمة المرور 🈴: <code>{password}</code>\n"
        f"كود السحب: <code>{withdraw_code}</code>\n"
        f"وسيلة الدفع 💳: <b>{method}</b>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        f"{method_info}\n\n"
        f"تحقق من توفر المبلغ وقم بقبول/رفض الطلب بناء على ذلك.\n"
    )


def stringify_process_withdraw_order(
    amount: float,
    serial: int,
    method: str,
    payment_method_number: str,
    *args,
):
    return (
        "تفاصيل طلب سحب :\n\n"
        f"المبلغ 💵: <code>{amount if amount else 'لا يوجد بعد'}</code>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        f"وسيلة الدفع: <code>{method}</code>\n\n"
        f"Payment Info: <code>{payment_method_number}</code>\n\n"
        "تنبيه: اضغط على رقم المحفظة والمبلغ لنسخها كما هي في الرسالة تفادياً للخطأ."
    )


def stringify_check_busdt_order(amount, method, serial, method_info):
    return (
        f"طلب شراء USDT جديد:\n\n"
        f"المبلغ💵: <code>{amount}</code> USDT\n"
        f"وسيلة الدفع 💳: <b>{method}</b>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        f"{method_info}\n"
    )


def stringify_process_busdt_order(
    amount: float,
    serial: int,
    method: str,
    payment_method_number: str,
    *args,
):
    return (
        "طلب شراء USDT جديد:\n\n"
        f"المبلغ 💵: <code>{amount if amount else 'لا يوجد بعد'}</code>\n\n"
        f"Serial: <code>{serial}</code>\n\n"
        f"وسيلة الدفع: <code>{method}</code>\n\n"
        f"Payment Info: <code>{payment_method_number}</code>\n\n"
        "تنبيه: اضغط على رقم المحفظة والمبلغ لنسخها كما هي في الرسالة تفادياً للخطأ."
    )


def stringify_returned_order(attachments: str, stringify_order, *args):
    order = stringify_order(*args)
    order += "<b>" + "\n\nطلب معاد، المرفقات:\n\n" + attachments + "</b>"
    return order
