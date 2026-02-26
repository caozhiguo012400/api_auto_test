# -*- coding:utf-8 -*-
"""
时间工具类（时间格式化、时间戳转换、时间计算等）
"""
import time
from datetime import datetime, timedelta
from typing import Union
from core.logger import log


class TimeUtil:
    """时间工具类"""

    # 常用时间格式
    FORMAT_TIMESTAMP = "%Y-%m-%d %H:%M:%S"  # 标准时间格式
    FORMAT_DATE = "%Y-%m-%d"  # 日期格式
    FORMAT_TIME = "%H:%M:%S"  # 时间格式
    FORMAT_COMPACT = "%Y%m%d%H%M%S"  # 紧凑格式（常用于文件名、订单号）

    @staticmethod
    def get_current_timestamp(format_str: str = FORMAT_TIMESTAMP) -> str:
        """
        获取当前时间戳（格式化字符串）
        :param format_str: 时间格式（默认：YYYY-MM-DD HH:MM:SS）
        :return: 格式化后的时间字符串
        """
        try:
            return datetime.now().strftime(format_str)
        except Exception as e:
            log.error(f"获取当前时间失败：{str(e)}")
            raise

    @staticmethod
    def get_current_unix_timestamp() -> int:
        """
        获取当前Unix时间戳（秒级）
        :return: Unix时间戳（整数）
        """
        return int(time.time())

    @staticmethod
    def get_current_unix_timestamp_ms() -> int:
        """
        获取当前Unix时间戳（毫秒级）
        :return: Unix时间戳（整数，毫秒）
        """
        return int(time.time() * 1000)

    @staticmethod
    def timestamp_to_datetime(timestamp: Union[int, str], format_str: str = FORMAT_TIMESTAMP) -> str:
        """
        时间戳转时间字符串
        :param timestamp: 时间戳（秒级或毫秒级）
        :param format_str: 目标时间格式
        :return: 格式化后的时间字符串
        """
        try:
            timestamp = int(timestamp)
            # 判断是秒级还是毫秒级时间戳（毫秒级通常大于10位）
            if timestamp > 9999999999:
                timestamp = timestamp / 1000
            return datetime.fromtimestamp(timestamp).strftime(format_str)
        except Exception as e:
            log.error(f"时间戳转换失败：{str(e)}，时间戳：{timestamp}")
            raise

    @staticmethod
    def datetime_to_timestamp(datetime_str: str, format_str: str = FORMAT_TIMESTAMP, unit: str = "s") -> int:
        """
        时间字符串转时间戳
        :param datetime_str: 时间字符串
        :param format_str: 时间格式
        :param unit: 时间戳单位（s=秒，ms=毫秒）
        :return: 时间戳（整数）
        """
        try:
            dt = datetime.strptime(datetime_str, format_str)
            timestamp = int(dt.timestamp())
            return timestamp * 1000 if unit == "ms" else timestamp
        except Exception as e:
            log.error(f"时间字符串转换失败：{str(e)}，时间字符串：{datetime_str}")
            raise

    @staticmethod
    def get_time_delta(days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0,
                      format_str: str = FORMAT_TIMESTAMP) -> str:
        """
        获取相对当前时间的偏移时间（未来或过去）
        :param days: 天数偏移（正数为未来，负数为过去）
        :param hours: 小时偏移
        :param minutes: 分钟偏移
        :param seconds: 秒偏移
        :param format_str: 返回时间格式
        :return: 偏移后的时间字符串
        """
        try:
            delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
            return (datetime.now() + delta).strftime(format_str)
        except Exception as e:
            log.error(f"计算时间偏移失败：{str(e)}")
            raise

    @staticmethod
    def get_date_range(start_date: str, end_date: str, format_str: str = FORMAT_DATE) -> list:
        """
        获取日期范围内的所有日期（包含起止日期）
        :param start_date: 开始日期（YYYY-MM-DD）
        :param end_date: 结束日期（YYYY-MM-DD）
        :param format_str: 日期格式
        :return: 日期列表
        """
        try:
            start_dt = datetime.strptime(start_date, format_str)
            end_dt = datetime.strptime(end_date, format_str)
            date_list = []
            current_dt = start_dt
            while current_dt <= end_dt:
                date_list.append(current_dt.strftime(format_str))
                current_dt += timedelta(days=1)
            return date_list
        except Exception as e:
            log.error(f"获取日期范围失败：{str(e)}")
            raise

    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        格式化时长（秒转易读格式）
        :param seconds: 时长（秒）
        :return: 格式化后的时长（如：1小时30分15秒）
        """
        try:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            result = []
            if hours > 0:
                result.append(f"{hours}小时")
            if minutes > 0:
                result.append(f"{minutes}分")
            if secs > 0 or not result:
                result.append(f"{secs}秒")
            return "".join(result)
        except Exception as e:
            log.error(f"格式化时长失败：{str(e)}")
            raise

    @staticmethod
    def sleep(seconds: float):
        """
        延时等待（封装time.sleep，增加日志）
        :param seconds: 等待秒数
        """
        log.info(f"等待{seconds}秒...")
        time.sleep(seconds)


# 导出实例，供外部使用
time_util = TimeUtil()


if __name__ == '__main__':
    # 测试代码
    print("当前时间:", time_util.get_current_timestamp())
    print("当前日期:", time_util.get_current_timestamp(TimeUtil.FORMAT_DATE))
    print("Unix时间戳:", time_util.get_current_unix_timestamp())
    print("Unix时间戳(毫秒):", time_util.get_current_unix_timestamp_ms())
    print("时间戳转时间:", time_util.timestamp_to_datetime(time_util.get_current_unix_timestamp()))
    print("明天此时:", time_util.get_time_delta(days=1))
    print("昨天此时:", time_util.get_time_delta(days=-1))
    print("日期范围:", time_util.get_date_range("2024-01-01", "2024-01-05"))
    print("格式化时长:", time_util.format_duration(3665))
