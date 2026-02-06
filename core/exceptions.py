# -*- coding:utf-8 -*-
from core.logger import log


# ------------------------------ 自定义异常类型（按场景分类）------------------------------
class ApiAutoTestError(BaseException):
    """框架基础异常（所有自定义异常的父类）"""

    def __init__(self, msg: str):
        self.msg = msg
        super().__init__(self.msg)
        log.error(f"【框架异常】{self.msg}")


class ConfigLoadError(ApiAutoTestError):
    """配置文件加载异常（如YAML/Excel读取失败、配置格式错误）"""

    def __init__(self, msg: str):
        super().__init__(f"配置加载失败：{msg}")


class ApiRequestError(ApiAutoTestError):
    """接口请求异常（如超时、连接失败、请求方法错误）"""

    def __init__(self, msg: str):
        super().__init__(f"接口请求异常：{msg}")
