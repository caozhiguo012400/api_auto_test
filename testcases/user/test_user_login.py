# -*- coding:utf-8 -*-
import pytest
from core.api_client import api_client
from core.assert_util import assert_util
from utils.file_util import file_util
from utils.common_util import get_global_token
from core.logger import log
# 读取登录接口测试数据（从YAML文件读取）
read_yaml = file_util.read_yaml()
login_test_data = read_yaml("data/test_data.yaml")["user"]["login"]


# ------------------------------ 常规用例（单条用例，基于YAML数据）------------------------------
def test_user_login_success(login_fixture):
    """
    正向用例：正确账号密码登录
    依赖夹具：login_fixture（登录获取token）
    """
    # 从夹具中获取token（也可通过get_global_token()获取）
    token = login_fixture
    assert token is not None, "登录失败，token为空"
    log.info("✅ 用例test_user_login_success执行完成，测试通过")


# ------------------------------ 数据驱动用例（批量用例，基于YAML数据参数化）------------------------------
@pytest.mark.parametrize("test_data", login_test_data)
def test_user_login_parametrize(test_data):
    """
    数据驱动用例：批量执行登录接口用例（正向+反向）
    参数化：从YAML文件读取多条用例数据
    """
    log.info(f"✅ 执行登录数据驱动用例：{test_data['case_id']} - {test_data['case_desc']}")
    # 执行登录接口
    response = api_client.request(
        method=test_data["request"]["method"],
        url=test_data["request"]["url"],
        json=test_data["request"].get("json")
    )
    # 执行断言（根据用例预期结果动态断言）
    assert_util.assert_status_code(response, test_data["expected"]["status_code"])
    # 断言JSON字段（遍历预期的json_key，逐一断言）
    for key, expected_value in test_data["expected"]["json_key"].items():
        if expected_value == "not_null":
            # 非空校验
            assert_util.assert_json_key_exists(response, key)
        else:
            # 等值校验
            assert_util.assert_json_key_value(response, key, expected_value)
    log.info(f"✅ 用例{test_data['case_id']}执行完成，测试通过")


# ------------------------------ 依赖数据库用例（接口+数据库双重校验）------------------------------
def test_user_register_db_check(db_fixture):
    """
    复杂用例：注册接口+数据库双重校验
    依赖夹具：db_fixture（初始化/清理测试数据）
    功能：执行注册接口，同时校验数据库中是否新增对应用户
    """
    log.info("✅ 执行注册接口+数据库校验用例")
    # 读取注册测试数据
    register_data = read_yaml("data/test_data.yaml")["user"].get("register", [])[0]
    # 替换测试数据中的动态参数（从db_fixture获取）
    register_data["request"]["json"]["username"] = db_fixture["username"]
    register_data["request"]["json"]["password"] = db_fixture["password"]
    register_data["request"]["json"]["mobile"] = db_fixture["mobile"]

    # 执行注册接口
    response = api_client.post(
        url=register_data["request"]["url"],
        json=register_data["request"]["json"]
    )
    # 接口断言
    assert_util.assert_status_code(response, register_data["expected"]["status_code"])
    assert_util.assert_json_key_value(response, "message", "注册成功")

    # 数据库断言（校验数据库中是否新增该用户）
    select_sql = read_yaml("data/sql_data/user_sql.yaml")["user"]["select_user_by_username"].format(
        username=db_fixture["username"]
    )
    db_result = db_client.query_one(select_sql)
    # 断言数据库结果（用户名、手机号一致）
    assert_util.assert_db_equal(db_result["username"], db_fixture["username"], msg="校验注册用户用户名")
    assert_util.assert_db_equal(db_result["mobile"], db_fixture["mobile"], msg="校验注册用户手机号")
    log.info("✅ 注册接口+数据库校验用例执行完成，测试通过")


# ------------------------------ Excel数据驱动用例（基于Excel批量执行）------------------------------
def test_user_login_excel(login_excel_data):
    """
    Excel数据驱动用例：从Excel读取批量用例数据，批量执行
    依赖夹具：login_excel_data（Excel数据参数化夹具）
    """
    case_id = login_excel_data["case_id"]
    case_desc = login_excel_data["case_desc"]
    log.info(f"✅ 执行Excel数据驱动用例：{case_id} - {case_desc}")

    # 构建请求参数（从Excel数据中读取）
    request_data = {
        "method": login_excel_data["method"],
        "url": login_excel_data["url"],
        "json": {
            "username": login_excel_data["username"],
            "password": login_excel_data["password"]
        }
    }

    # 执行登录接口
    response = api_client.request(
        method=request_data["method"],
        url=request_data["url"],
        json=request_data["json"]
    )

    # 执行断言（Excel中存储预期状态码和响应字段）
    expected_status_code = int(login_excel_data["expected_status_code"])
    expected_code = int(login_excel_data["expected_code"])
    expected_message = login_excel_data["expected_message"]

    assert_util.assert_status_code(response, expected_status_code)
    assert_util.assert_json_key_value(response, "code", expected_code)
    assert_util.assert_json_key_value(response, "message", expected_message)
    log.info(f"✅ 用例{case_id}执行完成，测试通过")