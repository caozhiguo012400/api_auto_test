# -*- coding:utf-8 -*-
from core.exceptions import ApiAutoTestError


# ------------------------------ 自定义异常类型（按场景分类）------------------------------


class AssertFailError(ApiAutoTestError):
    """断言失败异常（自定义断言，区别于pytest原生断言）"""

    def __init__(self, msg: str):
        super().__init__(f"断言失败：{msg}")


class DatabaseError(ApiAutoTestError):
    """数据库操作异常（如连接失败、SQL执行错误）"""

    def __init__(self, msg: str):
        super().__init__(f"数据库操作异常：{msg}")


class EncryptError(ApiAutoTestError):
    """加密解密异常（如密钥错误、算法不支持）"""

    def __init__(self, msg: str):
        super().__init__(f"加密解密异常：{msg}")


class DataNotFoundError(ApiAutoTestError):
    """测试数据未找到异常（如Excel/YAML中未找到指定用例数据）"""

    def __init__(self, msg: str):
        super().__init__(f"测试数据未找到：{msg}")


# ------------------------------ 全局异常捕获装饰器（用于用例、核心方法）------------------------------
def exception_catch(func):
    """
    全局异常捕获装饰器，用于捕获测试用例、核心方法中的异常，统一处理
    :param func: 被装饰的函数（用例方法、核心工具方法）
    :return: 函数执行结果（异常时返回None，记录错误日志）
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ApiAutoTestError as e:
            # 自定义异常，已在异常类中记录日志，此处直接抛出，让pytest捕获标记用例失败
            raise
        except Exception as e:
            # 未知异常，记录详细日志，抛出框架基础异常
            error_msg = f"未知异常：{str(e)}，函数：{func.__name__}，参数：{args} {kwargs}"
            raise ApiAutoTestError(error_msg) from e

    return wrapper
