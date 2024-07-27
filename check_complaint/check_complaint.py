from models import ComplaintConv
from user.complaint.common import stringify_order

def make_complaint_main_text(order_serial:int, order_type:str, reason:str):
    text = (
        f"شكوى جديدة:\n\n"
        f"{stringify_order(serial=order_serial, order_type=order_type)}\n\n"
        "سبب الشكوى:\n"
        f"<b>{reason}</b>\n\n"
    )

    return text


def make_conv_text(complaint_id:int):
    conv = ComplaintConv.get_conv(
        complaint_id=complaint_id
    )
    conv_text = ""
    for m in conv:
        if m.from_user:
            conv_text += f"رد المستخدم على الشكوى:\n<b>{m.msg}</b>\n\n"
        else:
            conv_text += f"رد الدعم على الشكوى:\n<b>{m.msg}</b>\n\n"
    
    return conv_text