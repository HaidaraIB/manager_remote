from telegram.ext import ContextTypes


def get_offer_info(context: ContextTypes.DEFAULT_TYPE, order_type: str):
    total = context.bot_data[f"{order_type}_offer_total"]
    p = context.bot_data[f"{order_type}_offer_percentage"]
    d = context.bot_data[f"{order_type}_offer_date"]
    min_amount = context.bot_data[f"{order_type}_offer_min_amount"]
    max_amount = context.bot_data[f"{order_type}_offer_max_amount"]
    msg_id = context.bot_data[f"{order_type}_offer_msg_id"]
    return total, p, d, min_amount, max_amount, msg_id