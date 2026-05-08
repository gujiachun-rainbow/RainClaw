import logging
from datetime import datetime, timezone, timedelta
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def current_datetime(timezone_offset: int = 8) -> dict:
    """获取当前时间、日期和星期几。

    当用户询问现在几点、今天几号、今天星期几、当前时间日期等信息时使用此工具。
    支持时区偏移设置，默认返回北京时间（东八区，UTC+8）。

    Args:
        timezone_offset: 时区偏移量（相对于UTC的小时数），默认8表示东八区（北京时间）。

    Returns:
        包含以下字段的字典：
        - datetime_str: 完整日期时间字符串，格式如 "2024-01-15 14:30:45"
        - date_str: 日期字符串，格式如 "2024-01-15"
        - time_str: 时间字符串，格式如 "14:30:45"
        - weekday: 星期几（中文），如 "星期一"、"星期二"等
        - weekday_number: 星期几的数字（1=星期一，7=星期日）
        - timezone: 时区描述
    """
    logger.info(f"[current_datetime] params: timezone_offset={timezone_offset}")

    # 创建带指定时区偏移的时区对象
    tz = timezone(timedelta(hours=timezone_offset))
    now = datetime.now(tz)

    # 星期几映射（中文）
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday_cn = weekdays[now.weekday()]
    weekday_num = now.weekday() + 1  # 1=星期一, 7=星期日

    # 时区描述
    if timezone_offset >= 0:
        tz_desc = f"UTC+{timezone_offset}"
    else:
        tz_desc = f"UTC{timezone_offset}"

    result = {
        "datetime_str": now.strftime("%Y-%m-%d %H:%M:%S"),
        "date_str": now.strftime("%Y-%m-%d"),
        "time_str": now.strftime("%H:%M:%S"),
        "weekday": weekday_cn,
        "weekday_number": weekday_num,
        "timezone": tz_desc,
    }

    logger.info(f"[current_datetime] result: {result}")
    return result
