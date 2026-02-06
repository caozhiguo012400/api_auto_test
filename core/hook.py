from core.logger import log
from core.exception_handler import EncryptError
from encrypt.encrypt_util import aes_encrypt, base64_encrypt
from encrypt.sign_util import generate_sign
from utils.common_util import get_global_token


def request_hook(method, full_url, kwargs):
    """
    请求前钩子（请求发送前执行）
    功能：参数加密、接口签名、token注入、请求头补充等
    :param method: 请求方法
    :param full_url: 完整请求地址
    :param kwargs: 请求参数（params、json、data、headers等）
    :return: 处理后的method、full_url、kwargs
    """
    # 1. 注入全局token（如果配置需要token）
    from core.api_client import api_client
    if api_client.config["api"]["need_token"]:
        token = get_global_token()  # 从全局变量中获取token（登录后存入）
        if token:
            token_key = api_client.config["api"]["token_key"]
            token_prefix = api_client.config["api"]["token_prefix"]
            kwargs["headers"][token_key] = f"{token_prefix}{token}"
            log.info(f"请求前钩子：注入全局token，{token_key}={token_prefix}***")

    # 2. 对请求参数进行加密（示例：AES加密json参数，可根据实际项目修改）
    if kwargs.get("json") and full_url.endswith("/encrypt/api"):
        try:
            encrypt_key = "1234567890abcdef"  # 实际项目中从配置文件读取，避免硬编码
            # 对json参数进行AES加密，再进行Base64编码
            encrypt_json = aes_encrypt(str(kwargs["json"]), encrypt_key)
            kwargs["json"] = {"encrypt_data": base64_encrypt(encrypt_json)}
            log.info(f"请求前钩子：对请求参数进行AES+Base64加密")
        except Exception as e:
            raise EncryptError(f"请求参数加密失败：{str(e)}")

    # 3. 接口签名（示例：生成请求签名，防重放、防篡改）
    if full_url.endswith("/sign/api"):
        # 生成签名（参数：请求参数、时间戳、随机字符串、密钥）
        sign_params = kwargs.get("params", {})
        sign = generate_sign(sign_params, "sign_key_123")  # 密钥从配置文件读取
        kwargs["params"]["sign"] = sign
        kwargs["params"]["timestamp"] = sign_params["timestamp"]
        kwargs["params"]["nonce"] = sign_params["nonce"]
        log.info(f"请求前钩子：生成接口签名，sign={sign}")

    return method, full_url, kwargs


def response_hook(response):
    """
    响应后钩子（请求返回后执行）
    功能：响应数据解密、响应状态码校验、响应数据格式化等
    :param response: 原始响应对象
    :return: 处理后的响应对象
    """
    # 1. 对响应数据进行解密（示例：AES解密响应数据，可根据实际项目修改）
    if response.url.endswith("/encrypt/api"):
        try:
            encrypt_key = "1234567890abcdef"
            # 从响应中获取加密数据，解密后替换原始响应内容
            encrypt_data = response.json().get("encrypt_data")
            if encrypt_data:
                decrypt_data = aes_encrypt(encrypt_data, encrypt_key, decrypt=True)
                # 替换响应的text和json方法，返回解密后的数据
                response._content = decrypt_data.encode("utf-8")
                log.info(f"响应后钩子：对响应数据进行AES解密")
        except Exception as e:
            raise EncryptError(f"响应数据解密失败：{str(e)}")

    # 2. 响应状态码预处理（如401表示token过期，自动重新登录）
    if response.status_code == 401:
        log.warning("响应后钩子：token过期，尝试重新登录获取token")
        # 调用登录方法，重新获取token（实际项目中需根据登录接口修改）
        from testcases.test_user.test_user_login import login
        login()
        # 重新发送当前请求（递归调用，最多重试1次）
        from core.api_client import api_client
        method = response.request.method
        url = response.request.url.replace(api_client.base_url, "")
        kwargs = {
            "headers": dict(response.request.headers),
            "params": dict(response.request.params),
            "json": response.request.json() if response.request.body else None
        }
        return api_client.request(method, url, **kwargs)

    return response
