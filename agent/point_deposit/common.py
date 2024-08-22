from user.work_with_us.common import syrian_govs_en_ar

def govs_pattern(callback_data: str):
    return callback_data in syrian_govs_en_ar
