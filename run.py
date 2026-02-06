# -*- coding:utf-8 -*-
"""
接口自动化测试框架执行入口
功能：一键执行测试用例、生成Allure报告、支持用例筛选、失败重试、日志输出
使用方式：python run.py （默认执行所有用例）
可选参数：--module 模块名（如user）、--case 用例名、--retry 重试次数、--report 报告路径
"""
import os
import sys
import argparse
import subprocess
from core.logger import init_logger, log
from utils.path_util import get_project_path, create_dir_if_not_exists, get_path
from config.config import run_config

# 初始化日志（程序启动即加载）
init_logger()


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="Python + Pytest + Allure 接口自动化测试框架")
    # 可选参数：测试模块（如user、order，对应testcases下的文件夹）
    parser.add_argument("--module", "-m", type=str, default="",
                        help="指定测试模块（如：--module user，仅执行用户模块用例）")
    # 可选参数：单个用例（如test_user_login.py::test_user_login_success）
    parser.add_argument("--case", "-c", type=str, default="",
                        help="指定单个测试用例（如：--case test_user_login.py::test_user_login_success）")
    # 可选参数：失败重试次数（默认1次，0表示不重试）
    parser.add_argument("--retry", "-r", type=int, default=run_config["retry_count"],
                        help=f"用例失败重试次数（默认{run_config["retry_count"]}次）")
    # 可选参数：Allure报告输出路径（默认report/allure-report）
    parser.add_argument("--report", "-p", type=str, default=run_config["allure_report_path"],
                        help=f"Allure报告输出路径（默认：{run_config["allure_report_path"]}）")
    # 可选参数：是否生成HTML报告（默认True）
    parser.add_argument("--html", type=bool, default=True,
                        help="是否生成HTML格式Allure报告（默认True）")
    return parser.parse_args()


def prepare_env():
    """准备测试环境
    1. 检查Python版本是否符合要求
    2. 创建Allure报告临时目录、日志目录（若不存在）
    """
    log.info("=" * 60)
    log.info("📌 开始准备测试环境")

    # 1. 检查Python版本
    python_version = sys.version_info[:2]
    required_version = (3, 8)  # 框架最低支持Python3.8
    if python_version < required_version:
        log.error(f"❌ Python版本不符合要求！当前版本：3.{python_version[1]}，需至少3.8版本")
        sys.exit(1)
    log.info(f"✅ Python版本校验通过：3.{python_version[1]}")

    # 2. 创建所需目录（Allure临时目录、报告目录、日志目录）
    create_dir_if_not_exists(get_path(run_config["allure_results_path"]))
    create_dir_if_not_exists(get_path(run_config["allure_report_path"]))
    create_dir_if_not_exists(get_path(run_config["log_dir"]))
    log.info(f"✅ 所需目录准备完成")
    log.info("=" * 60)


def build_run_command(args):
    """构建pytest执行命令"""
    log.info("📌 开始构建测试执行命令")

    # 基础命令（指定用例目录、Allure临时结果路径、失败重试）
    base_command = [
        "pytest",
        get_path("testcases"),  # 用例根目录
        f"--alluredir={get_path(run_config["allure_results_path"])}",  # Allure临时结果
        f"--reruns={args.retry}",  # 失败重试次数
        f"--reruns-delay=2",  # 重试间隔2秒
        "-v"  # 详细输出模式
    ]

    # 1. 筛选测试模块（--module参数）
    if args.module:
        module_path = get_path("testcases", f"test_{args.module}")
        if not os.path.exists(module_path):
            log.error(f"❌ 指定的测试模块不存在：{args.module}，路径：{module_path}")
            sys.exit(1)
        base_command.append(module_path)
        log.info(f"✅ 已筛选测试模块：{args.module}")

    # 2. 筛选单个测试用例（--case参数）
    if args.case:
        case_path = get_path("testcases", args.case)
        # 处理用例名（支持不带路径，自动拼接模块目录）
        if not os.path.exists(case_path):
            # 尝试拼接模块目录（如test_user_login.py → testcases/test_user/test_user_login.py）
            case_file = args.case.split("::")[0]
            for root, _, files in os.walk(get_path("testcases")):
                if case_file in files:
                    case_path = os.path.join(root, args.case)
                    break
            if not os.path.exists(case_path):
                log.error(f"❌ 指定的测试用例不存在：{args.case}")
                sys.exit(1)
        base_command.append(case_path)
        log.info(f"✅ 已指定单个测试用例：{args.case}")

    log.info(f"✅ 测试执行命令构建完成：{' '.join(base_command)}")
    return base_command


def run_tests(command):
    """执行测试用例"""
    log.info("=" * 60)
    log.info("🚀 开始执行接口自动化测试")
    log.info("=" * 60)

    try:
        # 执行pytest命令（实时输出日志）
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8"
        )
        # 输出测试执行结果
        for line in result.stdout.splitlines():
            log.info(line)
        log.info("=" * 60)
        log.info("✅ 所有测试用例执行完成（无失败/重试通过）")
        log.info("=" * 60)
    except subprocess.CalledProcessError as e:
        # 捕获执行异常（用例失败）
        log.error("=" * 60)
        log.error(f"❌ 测试用例执行完成，存在失败用例！")
        log.error(f"❌ 错误信息：{e.stdout}")
        log.error("=" * 60)
        # 不退出程序，继续生成报告
    except Exception as e:
        log.error("=" * 60)
        log.error(f"❌ 测试执行异常：{str(e)}")
        log.error("=" * 60)
        sys.exit(1)


def generate_allure_report(args):
    """生成Allure HTML报告"""
    log.info("=" * 60)
    log.info(f"📊 开始生成Allure测试报告")

    if not args.html:
        log.info("ℹ️  未开启HTML报告生成，跳过此步骤")
        log.info("=" * 60)
        return

    # 构建Allure报告生成命令
    report_command = [
        "allure",
        "generate",
        get_path(run_config["allure_results_path"]),  # 临时结果路径
        f"--output={get_path(args.report)}",  # 报告输出路径
        "--clean"  # 清理历史报告（避免报告冗余）
    ]

    try:
        # 执行报告生成命令
        subprocess.run(report_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        log.info(f"✅ Allure报告生成完成！报告路径：{get_path(args.report)}")
        log.info(f"✅ 可通过命令查看报告：allure open {get_path(args.report)}")
    except FileNotFoundError:
        log.error("❌ 生成Allure报告失败！未找到allure命令，请确保已安装Allure并配置环境变量")
    except subprocess.CalledProcessError as e:
        log.error(f"❌ 生成Allure报告失败！错误信息：{e.stderr}")
    finally:
        log.info("=" * 60)


def main():
    """主函数：串联整个测试流程"""
    try:
        # 1. 解析命令行参数
        args = parse_args()
        # 2. 准备测试环境
        prepare_env()
        # 3. 构建执行命令
        run_command = build_run_command(args)
        # 4. 执行测试用例
        run_tests(run_command)
        # 5. 生成测试报告
        generate_allure_report(args)

        log.info("🎉 接口自动化测试流程全部完成！")
        sys.exit(0)
    except Exception as e:
        log.error(f"❌ 测试流程执行异常：{str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    """程序入口"""
    main()
