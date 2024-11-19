from telegram.ext import ContextTypes


def get_offer_info(context: ContextTypes.DEFAULT_TYPE, order_type: str):
    total = context.bot_data[f"{order_type}_offer_total"]
    p = context.bot_data[f"{order_type}_offer_percentage"]
    h = context.bot_data[f"{order_type}_offer_hour"]
    min_amount = context.bot_data[f"{order_type}_offer_min_amount"]
    max_amount = context.bot_data[f"{order_type}_offer_max_amount"]
    return total, p, h, min_amount, max_amount