# -*- coding:utf-8 -*-
import pytest
from core.api_client import api_client
from db.db_client import db_client
from core.assert_util import assert_util
from utils.excel_util import excel_util
from utils.common_util import set_global_token, get_global_token
from data.sql_data.user_sql import user_sql
from encrypt.encrypt_util import md5_encrypt


# ------------------------------ 全局夹具（所有用例可用，自动执行）------------------------------
@pytest.fixture(scope="session", autouse=True)
def init_framework():
    """
    会话级夹具（整个测试会话只执行一次）
    功能：初始化框架，启动接口客户端、数据库客户端，测试结束后关闭资源
    """
    log.info("=" * 50)
    log.info("✅ 开始初始化接口自动化测试框架")
    # 初始化接口客户端（自动加载配置、创建会话）
    api_client
    # 初始化数据库客户端（自动连接数据库）
    db_client
    log.info("✅ 框架初始化完成，开始执行测试用例")
    log.info("=" * 50)

    # 测试结束后，关闭资源
    yield
    log.info("=" * 50)
    log.info("✅ 测试用例执行完成，开始清理资源")
    # 关闭接口会话
    api_client.close()
    # 关闭数据库连接
    db_client.close()
    log.info("✅ 资源清理完成，测试结束")
    log.info("=" * 50)


# ------------------------------ 接口依赖夹具（登录依赖，供需要token的用例使用）------------------------------
@pytest.fixture(scope="function")
def login_fixture():
    """
    函数级夹具（每个依赖的用例都执行一次）
    功能：执行登录接口，获取token并存入全局变量，供其他接口使用
    """
    log.info("📌 执行登录夹具：获取全局token")
    # 读取登录测试数据（从YAML文件读取）
    from utils.file_util import read_yaml
    login_data = read_yaml("data/test_data.yaml")["user"]["login"][0]  # 正向登录数据
    # 执行登录接口
    response = api_client.post(
        url=login_data["request"]["url"],
        json=login_data["request"]["json"]
    )
    # 断言登录成功
    assert_util.assert_status_code(response, login_data["expected"]["status_code"])
    assert_util.assert_json_key_value(response, "code", login_data["expected"]["json_key"]["code"])
    # 获取token并存入全局变量
    token = response.json()["data"]["token"]
    set_global_token(token)
    log.info(f"📌 登录成功，全局token已存入：{token[:10]}***")

    # 返回token（如需在用水例中直接使用，可通过yield返回）
    yield token

    # 可选：用例执行完成后，退出登录（根据项目需求决定）
    # api_client.post(url="/api/user/logout")
    # log.info("📌 执行登出操作，清除token")


# ------------------------------ 数据驱动夹具（Excel数据参数化，供批量用例使用）------------------------------
@pytest.fixture(scope="module", params=excel_util.read_excel_to_dict(sheet_name="login"))
def login_excel_data(request):
    """
    模块级夹具（每个模块只执行一次，参数化读取Excel中的登录用例数据）
    :param request: pytest内置参数，用于获取当前参数值
    :return: 单条Excel测试数据（字典格式）
    """
    log.info(f"📌 读取Excel测试数据：{request.param}")
    return request.param


# ------------------------------ 数据库夹具（测试前初始化数据，测试后清理数据）------------------------------
@pytest.fixture(scope="function")
def db_fixture():
    """
    函数级夹具（每个依赖的用例都执行一次）
    功能：测试前插入测试数据，测试后删除测试数据，避免用例污染
    """
    log.info("📌 执行数据库夹具：初始化测试数据")
    # 测试前：插入一条测试用户数据（加密密码）
    test_username = "test_fixture_user"
    test_password = md5_encrypt("123456")  # MD5加密密码
    test_mobile = "13800138001"
    insert_sql = user_sql["insert_user"].format(
        username=test_username,
        password=test_password,
        mobile=test_mobile
    )
    db_client.execute_sql(insert_sql)
    log.info(f"📌 数据库插入测试用户：{test_username}")

    # 返回测试用户信息（供用例使用）
    yield {
        "username": test_username,
        "password": "123456",  # 原始密码，供登录使用
        "mobile": test_mobile
    }

    # 测试后：删除测试用户数据（清理环境）
    delete_sql = user_sql["delete_user_by_username"].format(username=test_username)
    db_client.execute_sql(delete_sql)
    log.info(f"📌 数据库清理完成：删除测试用户{test_username}")


# ------------------------------ 自定义夹具（全局工具类实例，避免重复初始化）------------------------------
@pytest.fixture(scope="session")
def tools_fixture():
    """会话级夹具：导出常用工具类实例，供所有用例复用"""
    from utils.file_util import file_util
    from utils.random_util import random_util
    from utils.time_util import time_util
    yield {
        "file_util": file_util,
        "random_util": random_util,
        "time_util": time_util
    }