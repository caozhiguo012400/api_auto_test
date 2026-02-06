from loguru import logger
import os
import yaml
from utils.path_util import get_project_path
from core.exception_handler import ConfigLoadError

# 获取项目根路径
project_path = get_project_path()
# 读取日志配置
config_path = os.path.join(project_path, "config", "config.yaml")
try:
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)["log"]
except Exception as e:
    raise ConfigLoadError(f"读取日志配置失败：{str(e)}")

# 移除loguru默认日志处理器
logger.remove()

# 日志输出格式（包含时间、级别、模块、函数、行号、日志信息）
log_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {module}:{function}:{line} | {message}"

# 1. 控制台日志输出（可选，根据配置开关控制）
if config["is_console_output"]:
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=config["level"],
        format=log_format,
        colorize=True  # 控制台日志着色，提升可读性
    )

# 2. 文件日志输出（可选，按配置分割、保留）
if config["is_file_output"]:
    log_file_path = os.path.join(project_path, config["log_dir"], config["file_name"])
    # 确保日志目录存在
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    logger.add(
        sink=log_file_path,
        level=config["level"],
        format=log_format,
        rotation=config["rotation"],
        retention=config["retention"],
        encoding=config["encoding"],
        enqueue=True  # 异步写入日志，避免阻塞测试执行
    )

# 3. Allure日志输出（可选，将日志关联到Allure报告）
if config["is_allure_output"]:
    from allure_commons.utils import attach_file, md5
    from allure_commons.types import AttachmentType

    def allure_log_sink(msg):
        """将日志写入Allure报告（作为附件）"""
        log_content = msg.record["message"]
        log_level = msg.record["level"].name
        # 按日志级别生成不同的附件（可选，便于筛选）
        attach_file(
            source=log_content.encode("utf-8"),
            name=f"log_{log_level.lower()}_{md5(log_content)}.txt",
            attachment_type=AttachmentType.TEXT
        )

    logger.add(
        sink=allure_log_sink,
        level=config["level"],
        format=log_format
    )

# 导出日志实例，供外部所有模块使用
log = logger
if __name__ == '__main__':
    log.info("info信息")
    log.debug("debug信息")
    log.error("error信息")
    log.warning("warning信息")
    log.critical("critical严重错误信息")