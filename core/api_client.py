# -*- coding:utf-8 -*-
import requests
import yaml
import os
from core.logger import log
from core.exceptions import ApiRequestError, ConfigLoadError
from core.hook import request_hook, response_hook
from utils.path_util import get_project_path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class ApiClient:
    """接口请求客户端（封装所有HTTP请求，支持钩子、重试、代理、加密）"""

    def __init__(self):
        # 初始化会话（保持cookie、请求头复用）
        self.session = requests.Session()
        # 读取核心配置
        self.config = self._load_config()
        # 基础URL（当前环境）
        self.base_url = self.config["env"][self.config["env"]["current_env"]]["base_url"]
        # 超时时间
        self.timeout = self.config["framework"]["timeout"]
        # 代理配置
        self.proxy = self.config["env"][self.config["env"]["current_env"]]["proxy"]
        # 通用请求头
        self.common_headers = self.config["api"]["common_headers"]
        # 配置请求重试（连接失败、超时重试）
        # self._setup_retry()
        # 设置通用请求头
        self.session.headers.update(self.common_headers)

    def _load_config(self):
        """加载核心配置文件"""
        config_path = os.path.join(get_project_path(), "config", "config.yaml")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ConfigLoadError(f"加载核心配置文件config_path失败：{str(e)}")

    def _setup_retry(self):
        """配置请求重试（连接失败、超时、5xx状态码重试）"""
        retry_strategy = Retry(
            total=self.config["framework"]["retry_count"],  # 总重试次数
            backoff_factor=1,  # 重试间隔（1s、2s、4s...）
            status_forcelist=[429, 500, 502, 503, 504],  # 哪些状态码需要重试
            allowed_methods=["GET", "POST", "PUT", "DELETE"]  # 哪些请求方法需要重试
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _get_proxy(self):
        """获取代理配置（为空则不使用代理）"""
        if self.proxy:
            return {"http": self.proxy, "https": self.proxy}
        return None

    def request(self, method: str, url: str, **kwargs):
        """
        统一请求方法（核心），支持钩子函数、加密、代理、超时
        :param method: 请求方法（GET/POST/PUT/DELETE/UPLOAD等）
        :param url: 接口路径（如 /api/user/login，无需拼接基础URL）
        :param kwargs: 其他参数（params、json、data、headers、files、timeout等）
        :return: 响应对象（requests.Response）
        """
        # 1. 拼接完整URL
        full_url = self.base_url + url if not url.startswith("http") else url
        # 2. 设置超时时间（优先级：kwargs中的timeout > 全局配置）
        kwargs.setdefault("timeout", self.timeout)
        # 3. 设置代理
        kwargs.setdefault("proxies", self._get_proxy())
        # 4. 请求前钩子（如加密、token注入、参数处理）
        method, full_url, kwargs = request_hook(method, full_url, kwargs)
        # 5. 转换请求方法为大写（避免大小写错误）
        method = method.upper()

        try:
            log.info(f"=== 开始请求接口 ===")
            log.info(f"请求方法：{method}")
            log.info(f"请求地址：{full_url}")
            log.info(f"请求参数：{kwargs}")
            # 发送请求
            response = self.session.request(method, full_url, **kwargs)
            log.info(f"响应状态码：{response.status_code}")
            log.info(f"响应内容：{response.text}")
            log.info(f"=== 接口请求结束 ===\n")
            # 6. 响应后钩子（如解密、响应数据处理）
            response = response_hook(response)
            return response
        except requests.exceptions.Timeout:
            raise ApiRequestError(f"接口请求超时（超时时间：{kwargs['timeout']}s），地址：{full_url}")
        except requests.exceptions.ConnectionError:
            raise ApiRequestError(f"接口连接失败，地址：{full_url}（检查网络、代理配置）")
        # except requests.exceptions.InvalidMethod:
        #     raise ApiRequestError(f"请求方法错误：{method}（支持方法：GET/POST/PUT/DELETE等）")
        except Exception as e:
            raise ApiRequestError(f"接口请求异常：{str(e)}，地址：{full_url}")

    # ------------------------------ 封装常用请求方法（简化用例调用）------------------------------
    def get(self, url: str, **kwargs):
        """GET请求"""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs):
        """POST请求（支持json、data、files）"""
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs):
        """PUT请求"""
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs):
        """DELETE请求"""
        return self.request("DELETE", url, **kwargs)

    def upload(self, url: str, file_path: str, file_key: str = "file", **kwargs):
        """
        文件上传请求（简化文件上传操作）
        :param url: 接口路径
        :param file_path: 文件本地路径（如 ./data/test.jpg）
        :param file_key: 接口接收文件的key（如file、uploadFile）
        :param kwargs: 其他参数（headers、data等）
        :return: 响应对象
        """
        if not os.path.exists(file_path):
            raise ApiRequestError(f"文件上传失败：文件不存在，路径：{file_path}")
        # 构造文件参数
        files = {file_key: (os.path.basename(file_path), open(file_path, "rb"), "application/octet-stream")}
        # 设置请求头（文件上传需修改Content-Type）
        kwargs.setdefault("headers", {}).update({"Content-Type": "multipart/form-data"})
        return self.request("POST", url, files=files, **kwargs)

    def close(self):
        """关闭会话（释放资源）"""
        self.session.close()
        log.info("接口请求会话已关闭")


# 导出全局ApiClient实例（单例模式，避免重复初始化）
api_client = ApiClient()
