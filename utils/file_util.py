# -*- coding:utf-8 -*-
"""
文件操作工具类：
- 覆盖接口自动化常用的文件读写场景（JSON/YAML/Excel/普通文本）
- 兼容跨平台路径处理
- 封装异常处理，降低业务代码复杂度
"""
import os
import json
import yaml
import openpyxl
from pathlib import Path
from loguru import logger
from typing import Dict, List, Union, Any

# 项目根目录（自动适配，避免硬编码路径）
PROJECT_ROOT = Path(__file__).parent.parent
# 测试数据目录（统一管理测试数据文件）
TEST_DATA_DIR = PROJECT_ROOT / "test_data"
# 确保目录存在（避免文件写入时路径不存在报错）
os.makedirs(TEST_DATA_DIR, exist_ok=True)


class FileUtil:
    """文件操作工具类"""

    @staticmethod
    def get_abs_path(relative_path: str) -> str:
        """
        获取文件绝对路径（解决相对路径引用失败问题）
        :param relative_path: 相对项目根目录的路径（如 "test_data/login.yaml"）
        :return: 绝对路径字符串
        """
        abs_path = str(PROJECT_ROOT / relative_path)
        logger.debug(f"解析绝对路径：{relative_path} -> {abs_path}")
        return abs_path

    @staticmethod
    def read_text(file_path: str, encoding: str = "utf-8") -> str:
        """
        读取普通文本文件（如txt、csv等）
        :param file_path: 文件路径（支持相对/绝对路径）
        :param encoding: 编码格式
        :return: 文件内容字符串
        """
        try:
            abs_path = FileUtil.get_abs_path(file_path)
            with open(abs_path, "r", encoding=encoding) as f:
                content = f.read()
            logger.info(f"成功读取文本文件：{abs_path}")
            return content
        except Exception as e:
            logger.error(f"读取文本文件失败：{abs_path}，错误：{str(e)}")
            raise

    @staticmethod
    def write_text(
        file_path: str, content: str, encoding: str = "utf-8", mode: str = "w"
    ) -> None:
        """
        写入普通文本文件
        :param file_path: 文件路径（支持相对/绝对路径）
        :param content: 写入内容
        :param encoding: 编码格式
        :param mode: 写入模式（w=覆盖，a=追加）
        """
        try:
            abs_path = FileUtil.get_abs_path(file_path)
            # 自动创建父目录
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, mode, encoding=encoding) as f:
                f.write(content)
            logger.info(f"成功写入文本文件：{abs_path}")
        except Exception as e:
            logger.error(f"写入文本文件失败：{abs_path}，错误：{str(e)}")
            raise

    @staticmethod
    def read_json(file_path: str) -> Union[Dict, List]:
        """
        读取JSON文件（接口自动化常用：入参/预期结果存储）
        :param file_path: 文件路径（支持相对/绝对路径）
        :return: JSON解析后的字典/列表
        """
        try:
            abs_path = FileUtil.get_abs_path(file_path)
            with open(abs_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"成功读取JSON文件：{abs_path}，数据长度：{len(str(data))}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"JSON文件解析失败：{abs_path}，错误：{str(e)}")
            raise
        except Exception as e:
            logger.error(f"读取JSON文件失败：{abs_path}，错误：{str(e)}")
            raise

    @staticmethod
    def write_json(
        file_path: str, data: Union[Dict, List], indent: int = 4, ensure_ascii: bool = False
    ) -> None:
        """
        写入JSON文件（接口响应结果存储/数据驱动）
        :param file_path: 文件路径（支持相对/绝对路径）
        :param data: 要写入的字典/列表数据
        :param indent: 缩进（美化格式）
        :param ensure_ascii: 是否确保ASCII编码（False支持中文）
        """
        try:
            abs_path = FileUtil.get_abs_path(file_path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
            logger.info(f"成功写入JSON文件：{abs_path}")
        except Exception as e:
            logger.error(f"写入JSON文件失败：{abs_path}，错误：{str(e)}")
            raise

    @staticmethod
    def read_yaml(file_path: str) -> Union[Dict, List]:
        """
        读取YAML文件（接口自动化常用：配置/用例数据）
        :param file_path: 文件路径（支持相对/绝对路径）
        :return: YAML解析后的字典/列表
        """
        try:
            abs_path = FileUtil.get_abs_path(file_path)
            with open(abs_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            logger.info(f"成功读取YAML文件：{abs_path}，数据长度：{len(str(data))}")
            return data
        except yaml.YAMLError as e:
            logger.error(f"YAML文件解析失败：{abs_path}，错误：{str(e)}")
            raise
        except Exception as e:
            logger.error(f"读取YAML文件失败：{abs_path}，错误：{str(e)}")
            raise

    @staticmethod
    def read_excel(
        file_path: str, sheet_name: str = None, header_row: int = 0
    ) -> List[Dict[str, Any]]:
        """
        读取Excel文件（数据驱动：接口入参批量读取）
        :param file_path: 文件路径（支持相对/绝对路径）
        :param sheet_name: 工作表名称（None则读取第一个sheet）
        :param header_row: 表头行号（默认第1行）
        :return: 列表套字典（[{表头1: 值1, 表头2: 值2}, ...]）
        """
        try:
            abs_path = FileUtil.get_abs_path(file_path)
            workbook = openpyxl.load_workbook(abs_path, data_only=True)
            # 选择工作表
            sheet = workbook[sheet_name] if sheet_name else workbook.active
            # 获取表头
            headers = [cell.value for cell in sheet[header_row + 1]]
            # 读取数据行
            data = []
            for row in sheet.iter_rows(min_row=header_row + 2, values_only=True):
                row_dict = dict(zip(headers, row))
                # 过滤空行
                if any(row):
                    data.append(row_dict)
            workbook.close()
            logger.info(f"成功读取Excel文件：{abs_path}，sheet={sheet.title}，数据条数：{len(data)}")
            return data
        except Exception as e:
            logger.error(f"读取Excel文件失败：{abs_path}，错误：{str(e)}")
            raise


# 实例化（业务代码可直接导入使用，无需重复创建对象）
file_util = FileUtil()