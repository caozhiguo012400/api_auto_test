# -*- coding:utf-8 -*-
"""
随机工具类（生成随机数、随机字符串、随机日期等）
"""
import random
import string
from datetime import datetime, timedelta
from core.logger import log


class RandomUtil:
    """随机工具类"""

    @staticmethod
    def random_int(min_value: int = 0, max_value: int = 100) -> int:
        """
        生成随机整数
        :param min_value: 最小值（包含）
        :param max_value: 最大值（包含）
        :return: 随机整数
        """
        try:
            return random.randint(min_value, max_value)
        except Exception as e:
            log.error(f"生成随机整数失败：{str(e)}")
            raise

    @staticmethod
    def random_float(min_value: float = 0.0, max_value: float = 1.0, decimals: int = 2) -> float:
        """
        生成随机浮点数
        :param min_value: 最小值
        :param max_value: 最大值
        :param decimals: 保留小数位数
        :return: 随机浮点数
        """
        try:
            return round(random.uniform(min_value, max_value), decimals)
        except Exception as e:
            log.error(f"生成随机浮点数失败：{str(e)}")
            raise

    @staticmethod
    def random_string(length: int = 8, include_digits: bool = True, 
                     include_uppercase: bool = True, include_lowercase: bool = True,
                     include_special: bool = False) -> str:
        """
        生成随机字符串
        :param length: 字符串长度
        :param include_digits: 是否包含数字
        :param include_uppercase: 是否包含大写字母
        :param include_lowercase: 是否包含小写字母
        :param include_special: 是否包含特殊字符
        :return: 随机字符串
        """
        try:
            chars = ""
            if include_digits:
                chars += string.digits
            if include_uppercase:
                chars += string.ascii_uppercase
            if include_lowercase:
                chars += string.ascii_lowercase
            if include_special:
                chars += "!@#$%^&*"

            if not chars:
                chars = string.ascii_letters + string.digits

            return "".join(random.choice(chars) for _ in range(length))
        except Exception as e:
            log.error(f"生成随机字符串失败：{str(e)}")
            raise

    @staticmethod
    def random_phone() -> str:
        """
        生成随机手机号（中国大陆）
        :return: 随机手机号（如：13800138000）
        """
        # 手机号前缀
        prefixes = [
            "130", "131", "132", "133", "134", "135", "136", "137", "138", "139",
            "145", "147", "149", "150", "151", "152", "153", "155", "156", "157",
            "158", "159", "165", "166", "167", "170", "171", "172", "173", "174",
            "175", "176", "177", "178", "180", "181", "182", "183", "184", "185",
            "186", "187", "188", "189", "191", "198", "199"
        ]
        prefix = random.choice(prefixes)
        suffix = "".join(random.choice(string.digits) for _ in range(8))
        return prefix + suffix

    @staticmethod
    def random_email(domain: str = None) -> str:
        """
        生成随机邮箱地址
        :param domain: 邮箱域名（默认随机生成）
        :return: 随机邮箱地址（如：test_user@example.com）
        """
        if not domain:
            domains = ["qq.com", "163.com", "126.com", "gmail.com", "outlook.com", "hotmail.com"]
            domain = random.choice(domains)

        username = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
        return f"{username}@{domain}"

    @staticmethod
    def random_id_card() -> str:
        """
        生成随机身份证号（中国大陆，18位）
        :return: 随机身份证号
        """
        # 地区码（前6位，使用北京市朝阳区）
        area_code = "110105"
        # 出生日期（8位）
        birth_date = datetime.now() - timedelta(days=random.randint(18 * 365, 60 * 365))
        birth_str = birth_date.strftime("%Y%m%d")
        # 顺序码（3位）
        sequence = "".join(random.choice(string.digits) for _ in range(2)) + random.choice("012")
        # 校验码（1位）
        weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_codes = ["1", "0", "X", "9", "8", "7", "6", "5", "4", "3", "2"]

        id_17 = area_code + birth_str + sequence
        total = sum(int(id_17[i]) * weights[i] for i in range(17))
        check_code = check_codes[total % 11]

        return id_17 + check_code

    @staticmethod
    def random_date(start_date: str = None, end_date: str = None, 
                   format_str: str = "%Y-%m-%d") -> str:
        """
        生成随机日期
        :param start_date: 开始日期（默认：当前日期-30天）
        :param end_date: 结束日期（默认：当前日期）
        :param format_str: 日期格式
        :return: 随机日期字符串
        """
        try:
            if not end_date:
                end_date = datetime.now()
            else:
                end_date = datetime.strptime(end_date, format_str)

            if not start_date:
                start_date = end_date - timedelta(days=30)
            else:
                start_date = datetime.strptime(start_date, format_str)

            delta = end_date - start_date
            random_days = random.randint(0, delta.days)
            random_date = start_date + timedelta(days=random_days)

            return random_date.strftime(format_str)
        except Exception as e:
            log.error(f"生成随机日期失败：{str(e)}")
            raise

    @staticmethod
    def random_choice(items: list):
        """
        从列表中随机选择一个元素
        :param items: 列表
        :return: 随机选择的元素
        """
        if not items:
            raise ValueError("列表不能为空")
        return random.choice(items)

    @staticmethod
    def random_sample(items: list, k: int = 1) -> list:
        """
        从列表中随机选择k个元素（不重复）
        :param items: 列表
        :param k: 选择数量
        :return: 随机选择的元素列表
        """
        if not items:
            raise ValueError("列表不能为空")
        if k > len(items):
            raise ValueError(f"选择数量{k}不能超过列表长度{len(items)}")
        return random.sample(items, k)

    @staticmethod
    def random_shuffle(items: list) -> list:
        """
        随机打乱列表顺序
        :param items: 列表
        :return: 打乱后的列表
        """
        shuffled = items.copy()
        random.shuffle(shuffled)
        return shuffled


# 导出实例，供外部使用
random_util = RandomUtil()


if __name__ == '__main__':
    # 测试代码
    print("随机整数:", random_util.random_int(1, 100))
    print("随机浮点数:", random_util.random_float(0.0, 100.0, 2))
    print("随机字符串:", random_util.random_string(10))
    print("随机手机号:", random_util.random_phone())
    print("随机邮箱:", random_util.random_email())
    print("随机身份证:", random_util.random_id_card())
    print("随机日期:", random_util.random_date())
    print("随机选择:", random_util.random_choice(["A", "B", "C"]))
    print("随机采样:", random_util.random_sample([1, 2, 3, 4, 5], 3))
    print("随机打乱:", random_util.random_shuffle([1, 2, 3, 4, 5]))
