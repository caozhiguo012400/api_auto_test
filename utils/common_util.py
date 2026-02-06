# -*- coding:utf-8 -*-
"""通用工具类（与业务无关，全局复用）"""
from core.logger import log
from core.exception_handler import DataNotFoundError

# ------------------------------ 全局变量管理（用于存储接口依赖参数，如token、user_id）------------------------------
global_vars = {}  # 全局变量字典（存储token、user_id等依赖参数）


def set_global_token(token: str):
    """设置全局token（供所有接口使用）"""
    if not token:
        log.warning("设置全局token失败：token为空")
        return
    global_vars["token"] = token


def get_global_token() -> str:
    """获取全局token（从全局变量中读取）"""
    return global_vars.get("token", "")


def set_global_var(key: str, value):
    """设置全局变量（通用方法）"""
    if not key:
        raise DataNotFoundError("设置全局变量失败：key不能为空")
    global_vars[key] = value
    log.info(f"全局变量设置成功：{key} = {value}")


def get_global_var(key: str):
    """获取全局变量（通用方法）"""
    if not key:
        raise DataNotFoundError("获取全局变量失败：key不能为空")
    return global_vars.get(key, None)


# ------------------------------ 字典工具（排序、合并、取值）------------------------------
def sort_dict(dict_data: dict) -> dict:
    """字典按key升序排序（用于接口签名，避免参数顺序影响签名）"""
    if not isinstance(dict_data, dict):
        raise DataNotFoundError("字典排序失败：输入数据不是字典类型")
    return dict(sorted(dict_data.items(), key=lambda x: x[0]))


def merge_dict(dict1: dict, dict2: dict) -> dict:
    """合并两个字典（dict2覆盖dict1中相同的key，用于请求参数合并）"""
    if not isinstance(dict1, dict) or not isinstance(dict2, dict):
        raise DataNotFoundError("字典合并失败：输入数据必须是字典类型")
    merged_dict = dict1.copy()
    merged_dict.update(dict2)
    return merged_dict


def get_dict_value(dict_data: dict, key: str, default=None):
    """
    获取字典中的值（支持嵌套key，如data.user.id）
    :param dict_data: 目标字典
    :param key: 目标key（支持嵌套，用.分隔）
    :param default: 默认值（key不存在时返回）
    :return: 字典中的值（不存在则返回默认值）
    """
    if not isinstance(dict_data, dict):
        log.warning(f"获取字典值失败：输入数据不是字典类型，key：{key}")
        return default
    keys = key.split(".")
    current_data = dict_data
    for k in keys:
        if not isinstance(current_data, dict) or k not in current_data:
            log.warning(f"获取字典值失败：key「{k}」不存在于字典中，完整key：{key}")
            return default
        current_data = current_data[k]
    return current_data


# ------------------------------ 字符串工具（空值判断、替换）------------------------------
def is_empty(value) -> bool:
    """判断值是否为空（支持字符串、列表、字典、None）"""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, tuple, dict)) and len(value) == 0:
        return True
    return False


def str_replace(content: str, replace_map: dict) -> str:
    """
    字符串批量替换（用于动态参数替换，如${token}→实际token）
    :param content: 原始字符串
    :param replace_map: 替换字典（key：待替换字符串，value：替换后字符串）
    :return: 替换后的字符串
    """
    if not isinstance(content, str) or not isinstance(replace_map, dict):
        return content
    for old_str, new_str in replace_map.items():
        if old_str in content:
            content = content.replace(old_str, str(new_str))
    return content


# ------------------------------ 列表工具（去重、筛选）------------------------------
def list_deduplication(list_data: list) -> list:
    """列表去重（保留原始顺序）"""
    if not isinstance(list_data, list):
        raise DataNotFoundError("列表去重失败：输入数据不是列表类型")
    return list(dict.fromkeys(list_data))


def list_filter(list_data: list, condition) -> list:
    """
    列表筛选（根据条件筛选列表元素）
    :param list_data: 目标列表
    :param condition: 筛选条件（函数，如lambda x: x > 10）
    :return: 筛选后的列表
    """
    if not isinstance(list_data, list) or not callable(condition):
        raise DataNotFoundError("列表筛选失败：输入数据不是列表或条件不是可调用对象")
    return [item for item in list_data if condition(item)]
