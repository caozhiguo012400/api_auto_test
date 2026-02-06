import time
import random
import string
from core.logger import log
from core.exception_handler import EncryptError
from encrypt.encrypt_util import sha256_encrypt, md5_encrypt
from utils.common_util import sort_dict
from config.config import encrypt_config  # 直接导入加密配置


def generate_nonce(length: int = 16) -> str:
    """
    生成随机字符串（nonce，用于接口签名防重放，默认16位）
    :param length: 随机字符串长度
    :return: 随机字符串（字母+数字）
    """
    try:
        # 生成字母+数字的随机字符串
        chars = string.ascii_letters + string.digits
        return "".join(random.choice(chars) for _ in range(length))
    except Exception as e:
        raise EncryptError(f"生成nonce随机字符串失败：{str(e)}")


def generate_timestamp() -> int:
    """
    生成时间戳（秒级，用于接口签名防重放，与nonce配合使用）
    :return: 秒级时间戳（整数）
    """
    return int(time.time())


def generate_sign(params: dict, sign_key: str = None, sign_type: str = "sha256") -> str:
    """
    生成接口签名（防篡改、防重放，核心方法）
    签名逻辑：参数排序→拼接参数+时间戳+nonce+签名密钥→加密→得到签名
    :param params: 接口请求参数（字典）
    :param sign_key: 签名密钥（默认使用配置文件中的密钥）
    :param sign_type: 签名加密类型（md5/sha256，默认sha256）
    :return: 接口签名字符串
    """
    try:
        # 1. 校验参数和密钥
        if not isinstance(params, dict):
            raise EncryptError("接口签名失败：请求参数必须是字典类型")
        if not sign_key:
            sign_key = encrypt_config["sign_key"]
        if not sign_key:
            raise EncryptError("接口签名失败：签名密钥未配置")

        # 2. 补充时间戳和nonce（防重放）
        timestamp = generate_timestamp()
        nonce = generate_nonce()
        params["timestamp"] = timestamp
        params["nonce"] = nonce

        # 3. 排序参数（按key升序，避免参数顺序导致签名不一致）
        sorted_params = sort_dict(params)

        # 4. 拼接参数字符串（格式：key1=value1&key2=value2&...&timestamp=xxx&nonce=xxx&signKey=xxx）
        sign_str = ""
        for key, value in sorted_params.items():
            # 跳过空值参数（避免空值影响签名）
            if value is None or str(value).strip() == "":
                continue
            sign_str += f"{key}={value}&"
        # 拼接签名密钥（最后拼接，提升安全性）
        sign_str += f"signKey={sign_key}"

        # 5. 加密生成签名
        if sign_type.lower() == "md5":
            sign = md5_encrypt(sign_str, salt="")  # 签名加密无需额外加盐
        elif sign_type.lower() == "sha256":
            sign = sha256_encrypt(sign_str, salt="")
        else:
            raise EncryptError(f"不支持的签名加密类型：{sign_type}（支持：md5/sha256）")

        log.info(f"接口签名生成成功：签名字符串={sign_str}，签名={sign}，时间戳={timestamp}，nonce={nonce}")
        return sign
    except Exception as e:
        raise EncryptError(f"接口签名生成失败：{str(e)}，请求参数：{params}")


def verify_sign(params: dict, sign: str, sign_key: str = None, sign_type: str = "sha256", timeout: int = 300) -> bool:
    """
    验证接口签名（用于服务端校验，框架中可用于Mock接口或回调接口校验）
    :param params: 接口请求参数（包含timestamp、nonce）
    :param sign: 待验证的签名字符串
    :param sign_key: 签名密钥（与生成签名时一致）
    :param sign_type: 签名加密类型（与生成签名时一致）
    :param timeout: 签名有效期（秒，默认300秒=5分钟，防重放）
    :return: 验证结果（True=验证通过，False=验证失败）
    """
    try:
        # 1. 校验必要参数（timestamp、nonce）
        if "timestamp" not in params or "nonce" not in params:
            log.error("签名验证失败：参数缺少timestamp或nonce")
            return False

        # 2. 校验签名有效期（防止过期签名被复用）
        current_timestamp = generate_timestamp()
        request_timestamp = params["timestamp"]
        if abs(current_timestamp - request_timestamp) > timeout:
            log.error(
                f"签名验证失败：签名已过期（有效期{timeout}秒），当前时间戳={current_timestamp}，请求时间戳={request_timestamp}")
            return False

        # 3. 生成待验证的签名（使用相同的逻辑）
        generated_sign = generate_sign(params, sign_key, sign_type)

        # 4. 对比签名（大小写不敏感，兼容服务端可能的大小写处理）
        if generated_sign.lower() == sign.lower():
            log.info("接口签名验证通过")
            return True
        else:
            log.error(f"签名验证失败：生成的签名={generated_sign}，待验证签名={sign}")
            return False
    except Exception as e:
        log.error(f"签名验证异常：{str(e)}，请求参数：{params}，待验证签名：{sign}")
        return False
