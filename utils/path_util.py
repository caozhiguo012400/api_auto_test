# -*- coding:utf-8 -*-
"""路径工具类（跨平台路径处理，避免硬编码路径问题）"""
import os
from pathlib import Path
from core.exceptions import ConfigLoadError
from core.logger import log


def get_project_path() -> str:
    """
    获取项目根路径（自动识别，无需硬编码）
    原理：获取当前文件（path_util.py）的父目录的父目录，即项目根目录
    :return: 项目根路径（绝对路径，字符串格式）
    """
    try:
        # 获取当前文件的绝对路径
        current_file_path = Path(__file__).absolute()
        print(current_file_path)
        # 项目根目录是当前文件的父目录的父目录（utils→api_auto_test）
        project_path = current_file_path.parent.parent
        return str(project_path)
    except Exception as e:
        raise ConfigLoadError(f"获取项目根路径失败：{str(e)}")


def get_path(*args) -> str:
    """
    拼接路径（自动处理跨平台路径分隔符，如Windows\、Linux/）
    :param args: 路径片段（如"config", "config.yaml"）
    :return: 拼接后的绝对路径（字符串格式）
    """
    try:
        # 获取项目根路径
        project_path = get_project_path()
        # 拼接路径片段（*args接收多个参数，如get_path("data", "test_data.yaml")）
        target_path = os.path.join(project_path, *args)
        # 规范化路径（处理//、\\等问题）
        return os.path.normpath(target_path)
    except Exception as e:
        raise ConfigLoadError(f"路径拼接失败：{str(e)}，路径片段：{args}")


def check_path_exists(path: str) -> bool:
    """
    检查路径是否存在（支持文件、文件夹路径）
    :param path: 待检查的路径（相对路径/绝对路径）
    :return: 存在返回True，不存在返回False（不抛出异常）
    """
    try:
        # 若为相对路径，转换为绝对路径
        if not os.path.isabs(path):
            path = get_path(path)
        return os.path.exists(path)
    except Exception as e:
        log.warning(f"路径检查异常：{str(e)}，待检查路径：{path}")
        return False


def create_dir_if_not_exists(dir_path: str):
    """
    若文件夹不存在则创建（支持多级文件夹）
    :param dir_path: 文件夹路径（相对路径/绝对路径）
    """
    try:
        # 处理路径（相对路径转绝对路径）
        dir_path = get_path(dir_path) if not os.path.isabs(dir_path) else dir_path
        # 若文件夹不存在，创建多级文件夹
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            log.info(f"文件夹创建成功：{dir_path}")
        else:
            log.debug(f"文件夹已存在，无需创建：{dir_path}")
    except Exception as e:
        raise ConfigLoadError(f"文件夹创建失败：{str(e)}，文件夹路径：{dir_path}")


def get_file_name(path: str, with_suffix: bool = True) -> str:
    """
    从路径中提取文件名（支持带后缀/不带后缀）
    :param path: 文件路径（相对路径/绝对路径）
    :param with_suffix: 是否保留文件后缀（True=保留，False=不保留）
    :return: 提取的文件名
    """
    try:
        # 提取带后缀的文件名（如test_data.yaml）
        file_name = os.path.basename(path)
        # 若不需要后缀，去除后缀（如test_data）
        if not with_suffix:
            file_name = os.path.splitext(file_name)[0]
        return file_name
    except Exception as e:
        raise ConfigLoadError(f"提取文件名失败：{str(e)}，文件路径：{path}")


def get_file_dir(path: str) -> str:
    """
    从路径中提取文件所在的文件夹路径
    :param path: 文件路径（相对路径/绝对路径）
    :return: 文件所在的文件夹绝对路径
    """
    try:
        # 转换为绝对路径
        abs_path = get_path(path) if not os.path.isabs(path) else path
        # 提取文件夹路径
        file_dir = os.path.dirname(abs_path)
        return file_dir
    except Exception as e:
        raise ConfigLoadError(f"提取文件目录失败：{str(e)}，文件路径：{path}")


def get_all_files_in_dir(dir_path: str, suffix: str = None) -> list:
    """
    获取指定文件夹下所有文件（支持按后缀筛选）
    :param dir_path: 文件夹路径（相对路径/绝对路径）
    :param suffix: 文件后缀（如".yaml"、".xlsx"，None=获取所有文件）
    :return: 文件夹下所有符合条件的文件绝对路径列表（空文件夹返回空列表）
    """
    try:
        # 处理路径
        dir_path = get_path(dir_path) if not os.path.isabs(dir_path) else dir_path
        # 校验文件夹是否存在
        if not os.path.isdir(dir_path):
            raise ConfigLoadError(f"获取文件夹文件失败：{dir_path} 不是文件夹路径")
        # 遍历文件夹，获取所有文件
        all_files = []
        for root, _, files in os.walk(dir_path):
            for file in files:
                # 按后缀筛选（不区分大小写）
                if suffix is None or file.lower().endswith(suffix.lower()):
                    # 拼接文件绝对路径
                    file_path = os.path.join(root, file)
                    all_files.append(os.path.normpath(file_path))
        log.info(f"获取文件夹{dir_path}下符合条件的文件共{len(all_files)}个")
        return all_files
    except Exception as e:
        raise ConfigLoadError(f"获取文件夹文件失败：{str(e)}，文件夹路径：{dir_path}")


def delete_file_if_exists(file_path: str):
    """
    若文件存在则删除（不删除文件夹，避免误删）
    :param file_path: 文件路径（相对路径/绝对路径）
    """
    try:
        file_path = get_path(file_path) if not os.path.isabs(file_path) else file_path
        if os.path.exists(file_path) and os.path.isfile(file_path):
            os.remove(file_path)
            log.info(f"文件删除成功：{file_path}")
        else:
            log.debug(f"文件不存在或不是文件，无需删除：{file_path}")
    except Exception as e:
        raise ConfigLoadError(f"文件删除失败：{str(e)}，文件路径：{file_path}")


def get_file_size(path: str, unit: str = "B") -> float:
    """
    获取文件大小（支持不同单位转换）
    :param path: 文件路径（相对路径/绝对路径）
    :param unit: 单位（B/KB/MB/GB，默认B）
    :return: 文件大小（保留2位小数）
    """
    try:
        # 处理路径并校验文件是否存在
        file_path = get_path(path) if not os.path.isabs(path) else path
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            raise ConfigLoadError(f"获取文件大小失败：{file_path} 不是有效文件")
        # 获取文件大小（单位：B）
        file_size = os.path.getsize(file_path)
        # 单位转换
        unit = unit.upper()
        if unit == "KB":
            return round(file_size / 1024, 2)
        elif unit == "MB":
            return round(file_size / (1024 ** 2), 2)
        elif unit == "GB":
            return round(file_size / (1024 ** 3), 2)
        else:
            return round(file_size, 2)
    except Exception as e:
        raise ConfigLoadError(f"获取文件大小失败：{str(e)}，文件路径：{path}")


def copy_file(source_path: str, target_path: str, overwrite: bool = True):
    """
    复制文件（支持跨路径复制，可选择是否覆盖目标文件）
    :param source_path: 源文件路径（相对路径/绝对路径）
    :param target_path: 目标文件路径（相对路径/绝对路径）
    :param overwrite: 是否覆盖目标文件（True=覆盖，False=不覆盖，存在则报错）
    """
    try:
        # 处理源文件和目标文件路径
        source_abs = get_path(source_path) if not os.path.isabs(source_path) else source_path
        target_abs = get_path(target_path) if not os.path.isabs(target_path) else target_path
        # 校验源文件是否存在
        if not os.path.exists(source_abs) or not os.path.isfile(source_abs):
            raise ConfigLoadError(f"文件复制失败：{source_abs} 不是有效源文件")
        # 校验目标文件是否存在，是否覆盖
        if os.path.exists(target_abs) and not overwrite:
            raise ConfigLoadError(f"文件复制失败：目标文件{target_abs}已存在，未开启覆盖模式")
        # 创建目标文件所在文件夹（若不存在）
        create_dir_if_not_exists(os.path.dirname(target_abs))
        # 复制文件
        with open(source_abs, "rb") as src, open(target_abs, "wb") as dst:
            dst.write(src.read())
        log.info(f"文件复制成功：从{source_abs} 复制到 {target_abs}")
    except Exception as e:
        raise ConfigLoadError(f"文件复制失败：{str(e)}，源路径：{source_path}，目标路径：{target_path}")


if __name__ == '__main__':
    print(get_project_path())
