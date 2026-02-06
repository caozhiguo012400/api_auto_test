import hashlib
import base64
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad
from Crypto.Hash import SHA256
import os
from core.logger import log
from core.exception_handler import EncryptError
from utils.path_util import get_project_path
import yaml


# 读取加密配置（从config.yaml中获取，避免硬编码密钥）
def load_encrypt_config():
    config_path = os.path.join(get_project_path(), "config", "config.yaml")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)["encrypt"]
    except Exception as e:
        raise EncryptError(f"加载加密配置失败：{str(e)}")


encrypt_config = load_encrypt_config()


# ------------------------------ 基础加密算法（MD5、SHA256）------------------------------
def md5_encrypt(content: str, salt: str = None) -> str:
    """
    MD5加密（支持加盐，提升安全性）
    :param content: 待加密内容（字符串）
    :param salt: 盐值（默认使用配置文件中的盐值）
    :return: 加密后的16位/32位字符串（默认32位）
    """
    try:
        # 若未传盐值，使用配置文件中的默认盐值
        if not salt:
            salt = encrypt_config["md5_salt"]
        # 拼接内容和盐值，编码为UTF-8
        encrypt_content = f"{content}{salt}".encode("utf-8")
        # MD5加密
        md5 = hashlib.md5()
        md5.update(encrypt_content)
        # 返回32位小写加密结果（如需16位，取[8:24]）
        return md5.hexdigest()
    except Exception as e:
        raise EncryptError(f"MD5加密失败：{str(e)}，待加密内容：{content}")


def sha256_encrypt(content: str, salt: str = None) -> str:
    """
    SHA256加密（不可逆，适用于密码加密存储）
    :param content: 待加密内容（字符串）
    :param salt: 盐值（默认使用配置文件中的盐值）
    :return: 加密后的64位字符串
    """
    try:
        if not salt:
            salt = encrypt_config["sha256_salt"]
        encrypt_content = f"{content}{salt}".encode("utf-8")
        sha256 = hashlib.sha256()
        sha256.update(encrypt_content)
        return sha256.hexdigest()
    except Exception as e:
        raise EncryptError(f"SHA256加密失败：{str(e)}，待加密内容：{content}")


# ------------------------------ Base64编码/解码（辅助加密）------------------------------
def base64_encrypt(content: str) -> str:
    """
    Base64编码（可逆，常用于加密后内容转义，避免特殊字符）
    :param content: 待编码内容（字符串）
    :return: 编码后的Base64字符串
    """
    try:
        return base64.b64encode(content.encode("utf-8")).decode("utf-8")
    except Exception as e:
        raise EncryptError(f"Base64编码失败：{str(e)}，待编码内容：{content}")


def base64_decrypt(content: str) -> str:
    """
    Base64解码（对应base64_encrypt）
    :param content: 待解码的Base64字符串
    :return: 解码后的原始字符串
    """
    try:
        return base64.b64decode(content.encode("utf-8")).decode("utf-8")
    except Exception as e:
        raise EncryptError(f"Base64解码失败：{str(e)}，待解码内容：{content}")


# ------------------------------ AES加密/解密（对称加密，常用）------------------------------
def aes_encrypt(content: str, key: str = None, iv: str = None, decrypt: bool = False) -> str:
    """
    AES加密/解密（对称加密，支持CBC模式，16位密钥对应AES-128）
    :param content: 待加密/解密内容（字符串）
    :param key: 密钥（默认使用配置文件中的AES密钥，16位/24位/32位对应不同加密级别）
    :param iv: 向量（CBC模式必需，默认使用配置文件中的iv，16位）
    :param decrypt: 是否解密（False=加密，True=解密）
    :return: 加密/解密后的字符串
    """
    try:
        # 加载配置中的密钥和向量
        if not key:
            key = encrypt_config["aes_key"]
        if not iv:
            iv = encrypt_config["aes_iv"]
        # 校验密钥和向量长度（AES-128需16位，AES-192需24位，AES-256需32位）
        if len(key) not in [16, 24, 32]:
            raise EncryptError(f"AES密钥长度错误：需16/24/32位，当前{len(key)}位")
        if len(iv) != 16:
            raise EncryptError(f"AES IV向量长度错误：需16位，当前{len(iv)}位")

        # 编码密钥和向量为UTF-8
        key_bytes = key.encode("utf-8")
        iv_bytes = iv.encode("utf-8")
        # 初始化AES加密器/解密器（CBC模式，PKCS7填充）
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)

        if not decrypt:
            # 加密：填充内容→加密→Base64编码（避免特殊字符）
            content_bytes = content.encode("utf-8")
            # 填充内容至密钥整数倍长度（PKCS7填充）
            padded_content = pad(content_bytes, AES.block_size)
            encrypt_bytes = cipher.encrypt(padded_content)
            return base64_encrypt(encrypt_bytes.decode("latin-1"))
        else:
            # 解密：Base64解码→解密→去除填充
            decrypt_bytes = base64.b64decode(content.encode("utf-8"))
            decrypted_bytes = cipher.decrypt(decrypt_bytes)
            # 去除填充，获取原始内容
            content_bytes = unpad(decrypted_bytes, AES.block_size)
            return content_bytes.decode("utf-8")
    except Exception as e:
        operation = "解密" if decrypt else "加密"
        raise EncryptError(f"AES{operation}失败：{str(e)}，待{operation}内容：{content}")


# ------------------------------ RSA加密/解密（非对称加密，适用于敏感信息）------------------------------
def load_rsa_key(private_key_path: str = None, public_key_path: str = None) -> tuple:
    """
    加载RSA公私钥（从文件中读取，默认使用配置文件中的路径）
    :param private_key_path: 私钥路径（用于解密、签名）
    :param public_key_path: 公钥路径（用于加密、验签）
    :return: (私钥对象, 公钥对象)（未传路径则对应对象为None）
    """
    try:
        private_key = None
        public_key = None
        # 加载私钥
        if not private_key_path:
            private_key_path = encrypt_config["rsa_private_key_path"]
        if private_key_path and os.path.exists(private_key_path):
            with open(private_key_path, "r", encoding="utf-8") as f:
                private_key = RSA.importKey(f.read())
        # 加载公钥
        if not public_key_path:
            public_key_path = encrypt_config["rsa_public_key_path"]
        if public_key_path and os.path.exists(public_key_path):
            with open(public_key_path, "r", encoding="utf-8") as f:
                public_key = RSA.importKey(f.read())
        return private_key, public_key
    except Exception as e:
        raise EncryptError(f"加载RSA密钥失败：{str(e)}")


def rsa_encrypt(content: str, public_key: object = None) -> str:
    """
    RSA加密（非对称加密，用公钥加密，私钥解密，适用于敏感信息如密码、密钥）
    :param content: 待加密内容（字符串，长度不能超过密钥长度-11位）
    :param public_key: 公钥对象（默认自动加载配置文件中的公钥）
    :return: 加密后的Base64字符串
    """
    try:
        # 加载公钥
        if not public_key:
            _, public_key = load_rsa_key()
        if not public_key:
            raise EncryptError("RSA公钥未找到，请检查公钥路径或配置")
        # 初始化加密器
        cipher = PKCS1_v1_5.new(public_key)
        # 加密→Base64编码
        encrypt_bytes = cipher.encrypt(content.encode("utf-8"))
        return base64_encrypt(encrypt_bytes.decode("latin-1"))
    except Exception as e:
        raise EncryptError(f"RSA加密失败：{str(e)}，待加密内容：{content}")


def rsa_decrypt(content: str, private_key: object = None) -> str:
    """
    RSA解密（对应rsa_encrypt，用私钥解密）
    :param content: 待解密的Base64字符串
    :param private_key: 私钥对象（默认自动加载配置文件中的私钥）
    :return: 解密后的原始字符串
    """
    try:
        # 加载私钥
        if not private_key:
            private_key, _ = load_rsa_key()
        if not private_key:
            raise EncryptError("RSA私钥未找到，请检查私钥路径或配置")
        # 初始化解密器
        cipher = PKCS1_v1_5.new(private_key)
        # Base64解码→解密
        decrypt_bytes = base64.b64decode(content.encode("utf-8"))
        content_bytes = cipher.decrypt(decrypt_bytes, None)
        if not content_bytes:
            raise EncryptError("RSA解密失败：私钥不匹配或内容被篡改")
        return content_bytes.decode("utf-8")
    except Exception as e:
        raise EncryptError(f"RSA解密失败：{str(e)}，待解密内容：{content}")


# ------------------------------ 自定义加密（可根据项目扩展）------------------------------
def custom_encrypt(content: str, encrypt_type: str = "md5") -> str:
    """
    自定义加密入口（统一加密调用，便于后续扩展）
    :param content: 待加密内容
    :param encrypt_type: 加密类型（md5/sha256/aes/rsa）
    :return: 加密后的字符串
    """
    encrypt_type = encrypt_type.lower()
    if encrypt_type == "md5":
        return md5_encrypt(content)
    elif encrypt_type == "sha256":
        return sha256_encrypt(content)
    elif encrypt_type == "aes":
        return aes_encrypt(content)
    elif encrypt_type == "rsa":
        return rsa_encrypt(content)
    else:
        raise EncryptError(f"不支持的加密类型：{encrypt_type}（支持：md5/sha256/aes/rsa）")