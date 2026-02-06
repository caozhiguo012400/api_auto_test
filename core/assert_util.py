from core.logger import log
from core.exception_handler import AssertFailError
import json
from jsonschema import validate, ValidationError  # JSON Schema校验（需安装jsonschema）


class AssertUtil:
    """断言工具类（封装所有常用断言，支持自定义断言）"""

    # ------------------------------ 基础断言（响应码、响应内容）------------------------------
    @staticmethod
    def assert_status_code(response, expected_code: int):
        """
        断言响应状态码
        :param response: 响应对象（requests.Response）
        :param expected_code: 预期状态码（如200、201、400）
        """
        actual_code = response.status_code
        try:
            assert actual_code == expected_code, \
                f"状态码断言失败：预期{expected_code}，实际{actual_code}，响应内容：{response.text}"
            log.info(f"✅ 状态码断言成功：实际{actual_code} == 预期{expected_code}")
        except AssertionError as e:
            raise AssertFailError(str(e))

    @staticmethod
    def assert_response_contains(response, expected_content: str):
        """
        断言响应内容包含指定字符串（适用于非JSON响应）
        :param response: 响应对象
        :param expected_content: 预期包含的字符串
        """
        try:
            assert expected_content in response.text, \
                f"响应内容包含断言失败：预期包含「{expected_content}」，实际响应：{response.text}"
            log.info(f"✅ 响应内容包含断言成功：响应包含「{expected_content}」")
        except AssertionError as e:
            raise AssertFailError(str(e))

    @staticmethod
    def assert_response_not_contains(response, unexpected_content: str):
        """
        断言响应内容不包含指定字符串
        :param response: 响应对象
        :param unexpected_content: 预期不包含的字符串
        """
        try:
            assert unexpected_content not in response.text, \
                f"响应内容不包含断言失败：预期不包含「{unexpected_content}」，实际响应包含"
            log.info(f"✅ 响应内容不包含断言成功：响应不包含「{unexpected_content}」")
        except AssertionError as e:
            raise AssertFailError(str(e))

    # ------------------------------ JSON响应断言（最常用）------------------------------
    @staticmethod
    def assert_json_key_exists(response, expected_key: str):
        """
        断言JSON响应中包含指定key（支持嵌套key，如 data.user.id）
        :param response: 响应对象
        :param expected_key: 预期存在的key（如 "name"、"data.user.id"）
        """
        try:
            json_data = response.json()
            # 处理嵌套key（如 data.user.id）
            keys = expected_key.split(".")
            current_data = json_data
            for key in keys:
                current_data = current_data[key]
            log.info(f"✅ JSON key断言成功：响应包含key「{expected_key}」，值为「{current_data}」")
        except (ValueError, KeyError) as e:
            raise AssertFailError(f"JSON key断言失败：响应不包含key「{expected_key}」，错误：{str(e)}")

    @staticmethod
    def assert_json_key_value(response, expected_key: str, expected_value):
        """
        断言JSON响应中指定key的值等于预期值（支持嵌套key）
        :param response: 响应对象
        :param expected_key: 预期key（支持嵌套）
        :param expected_value: 预期值
        """
        try:
            json_data = response.json()
            keys = expected_key.split(".")
            current_data = json_data
            for key in keys:
                current_data = current_data[key]
            actual_value = current_data
            assert actual_value == expected_value, \
                f"JSON key值断言失败：key「{expected_key}」，预期{expected_value}，实际{actual_value}"
            log.info(f"✅ JSON key值断言成功：key「{expected_key}」，实际{actual_value} == 预期{expected_value}")
        except (ValueError, KeyError) as e:
            raise AssertFailError(f"JSON key值断言失败：响应不包含key「{expected_key}」，错误：{str(e)}")
        except AssertionError as e:
            raise AssertFailError(str(e))

    @staticmethod
    def assert_json_schema(response, schema: dict):
        """
        断言JSON响应符合指定的JSON Schema（用于校验响应格式、字段类型）
        :param response: 响应对象
        :param schema: JSON Schema字典（如 {"type": "object", "properties": {"name": {"type": "string"}}}）
        """
        try:
            json_data = response.json()
            validate(instance=json_data, schema=schema)
            log.info(f"✅ JSON Schema断言成功：响应格式符合预期Schema")
        except ValueError as e:
            raise AssertFailError(f"JSON Schema断言失败：响应不是合法JSON，错误：{str(e)}")
        except ValidationError as e:
            raise AssertFailError(f"JSON Schema断言失败：响应格式不符合预期，错误：{str(e)}")

    # ------------------------------ 数据库断言（接口响应与数据库比对）------------------------------
    @staticmethod
    def assert_db_equal(db_result, expected_result, msg: str = ""):
        """
        断言数据库查询结果等于预期结果
        :param db_result: 数据库查询结果（单个值/列表/字典）
        :param expected_result: 预期结果
        :param msg: 断言描述（可选）
        """
        try:
            assert db_result == expected_result, \
                f"数据库断言失败：{msg}，预期{expected_result}，实际{db_result}"
            log.info(f"✅ 数据库断言成功：{msg}，实际{db_result} == 预期{expected_result}")
        except AssertionError as e:
            raise AssertFailError(str(e))

    @staticmethod
    def assert_db_contains(db_result, expected_content, msg: str = ""):
        """
        断言数据库查询结果包含指定内容（适用于列表结果）
        :param db_result: 数据库查询结果（列表）
        :param expected_content: 预期包含的内容
        :param msg: 断言描述（可选）
        """
        try:
            assert expected_content in db_result, \
                f"数据库包含断言失败：{msg}，预期包含{expected_content}，实际{db_result}"
            log.info(f"✅ 数据库包含断言成功：{msg}，实际{db_result} 包含 {expected_content}")
        except AssertionError as e:
            raise AssertFailError(str(e))

    # ------------------------------ 自定义断言（灵活扩展）------------------------------
    @staticmethod
    def assert_custom(condition: bool, msg: str):
        """
        自定义断言（满足任意条件断言）
        :param condition: 断言条件（布尔值）
        :param msg: 断言失败提示信息
        """
        try:
            assert condition, msg
            log.info(f"✅ 自定义断言成功：{msg.split('，')[0]}")
        except AssertionError as e:
            raise AssertFailError(str(e))


# 导出断言实例，供外部使用
assert_util = AssertUtil()
