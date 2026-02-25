# -*- coding:utf-8 -*-
"""
文件操作工具类：（JSON/YAML/Excel/普通文本）
"""
import os
import json
import yaml
import openpyxl
from pathlib import Path
from core.logger import log
from typing import Dict, List, Union, Any

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


class FileUtil:
    """文件操作工具类"""

    @staticmethod
    def read_text(file_path: str, encoding: str = "utf-8") -> str:
        """
        读取普通文本文件（如txt、csv等）
        :param file_path: 文件路径（支持相对/绝对路径）
        :param encoding: 编码格式
        :return: 文件内容字符串
        """
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()
            log.info(f"成功读取文本文件：{file_path}")
            return content
        except Exception as e:
            log.error(f"读取文本文件失败：{file_path}，错误：{str(e)}")
            raise

    @staticmethod
    def write_text(file_path: str, content: str, encoding: str = "utf-8", mode: str = "w") -> None:
        """
        写入普通文本文件
        :param file_path: 文件路径（绝对路径）
        :param content: 写入内容
        :param encoding: 编码格式
        :param mode: 写入模式（w=覆盖，a=追加）
        """
        try:
            # 自动创建父目录
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, mode, encoding=encoding) as f:
                f.write(content)
            log.info(f"成功写入文本文件：{file_path}")
        except PermissionError:
            log.error(f"写入文本文件失败：{file_path}，错误：需传具体文件路径，而非文件夹路径")
            raise
        except Exception as e:
            log.error(f"写入文本文件失败：{file_path}，错误：{str(e)}")
            raise

    @staticmethod
    def read_json(file_path: str) -> Union[Dict, List]:
        """
        读取JSON文件
        :param file_path: 文件路径（绝对路径）
        :return: JSON解析后的字典/列表
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            log.info(f"成功读取JSON文件：{file_path}，数据长度：{len(str(data))}")
            return data
        except json.JSONDecodeError as e:
            log.error(f"JSON文件解析失败：{file_path}，错误：{str(e)}")
            raise
        except Exception as e:
            log.error(f"读取JSON文件失败：{file_path}，错误：{str(e)}")
            raise

    @staticmethod
    def write_json(file_path: str, data: Union[Dict, List], indent: int = 4, ensure_ascii: bool = False) -> None:
        """
        写入JSON文件
        :param file_path: 文件路径（支持相对/绝对路径）
        :param data: 要写入的字典/列表数据
        :param indent: 缩进
        :param ensure_ascii: 是否确保ASCII编码（False支持中文）
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
            log.info(f"成功写入JSON文件：{file_path}")
        except Exception as e:
            log.error(f"写入JSON文件失败：{file_path}，错误：{str(e)}")
            raise

    @staticmethod
    def read_yaml(file_path: str) -> Union[Dict, List]:
        """
        读取YAML文件（接口自动化常用：配置/用例数据）
        :param file_path: 文件路径（支持相对/绝对路径）
        :return: YAML解析后的字典/列表
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            log.info(f"成功读取Yaml文件：{file_path}")
            log.info(f"Yaml文件数据：{(str(data))}")
            return data
        except yaml.YAMLError as e:
            log.error(f"Yaml文件解析失败：{file_path}，错误：{str(e)}")
            raise
        except Exception as e:
            log.error(f"读取Yaml文件失败：{file_path}，错误：{str(e)}")
            raise

    @staticmethod
    def read_excel(file_path: str, sheet_name: str = None, header_row: int = 0) -> List[Dict[str, Any]]:
        """
        读取Excel文件
        :param file_path: 文件路径（绝对路径）
        :param sheet_name: 工作表名称（None则读取第一个sheet）
        :param header_row: 表头行号（默认第1行）
        :return: 列表套字典（[{表头1: 值1, 表头2: 值2}, ...]）
        """
        try:
            workbook = openpyxl.load_workbook(file_path, data_only=True)
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
            log.info(f"成功读取Excel文件：{file_path}，sheet={sheet.title}，数据条数：{len(data)}")
            return data
        except Exception as e:
            log.error(f"读取Excel文件失败：{file_path}，错误：{str(e)}")
            raise


# 实例化（业务代码可直接导入使用，无需重复创建对象）
file_util = FileUtil()

# if __name__ == '__main__':
#     print(file_util.read_excel(r"E:\易家项目资料\006案件解析系统\12.26债权原始资料\FM1105\1-200.xlsx"))
#     print(file_util.read_text(r"C:\Users\Administrator\Desktop\SQLite加密密码.txt"))
#     file_util.write_text(r"C:\Users\Administrator\Desktop\aaa.txt", "写入内容")
