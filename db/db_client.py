import yaml
import os
import pymysql
# import cx_Oracle
import psycopg2
from core.logger import log
from core.exception_handler import DatabaseError, ConfigLoadError
from utils.path_util import get_project_path
from dotenv import load_dotenv  # 加载环境变量（敏感配置）

# 加载环境变量（从.env文件读取敏感配置，如数据库密码）
load_dotenv(os.path.join(get_project_path(), ".env"))


class DbClient:
    """数据库客户端（支持MySQL、Oracle、PostgreSQL，封装CRUD操作）"""

    def __init__(self):
        # 加载数据库配置
        self.config = self._load_db_config()
        # 当前数据库配置
        self.current_db_config = self.config["db_env"][self.config["db_env"]["current_db"]]
        # 数据库连接对象
        self.conn = None
        # 数据库游标对象
        self.cursor = None
        # 连接数据库
        self._connect()

    def _load_db_config(self):
        """加载数据库配置文件"""
        db_config_path = os.path.join(get_project_path(), "db", "db_config.yaml")
        try:
            with open(db_config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                # 替换环境变量（敏感配置，如密码）
                for db_key, db_info in config["db_env"].items():
                    if isinstance(db_info, dict) and "password" in db_info:
                        if db_info["password"].startswith("${") and db_info["password"].endswith("}"):
                            env_key = db_info["password"][2:-1]
                            db_info["password"] = os.getenv(env_key, "")
                            if not db_info["password"]:
                                raise ConfigLoadError(f"环境变量{env_key}未配置（数据库密码）")
            return config
        except Exception as e:
            raise ConfigLoadError(f"加载数据库配置失败：{str(e)}")

    def _connect(self):
        """连接数据库（根据数据库类型选择对应驱动）"""
        db_type = self.current_db_config["type"].lower()
        try:
            if db_type == "mysql":
                # 连接MySQL
                self.conn = pymysql.connect(
                    host=self.current_db_config["host"],
                    port=self.current_db_config["port"],
                    user=self.current_db_config["user"],
                    password=self.current_db_config["password"],
                    database=self.current_db_config["database"],
                    charset=self.current_db_config["charset"],
                    connect_timeout=self.current_db_config["connect_timeout"],
                    cursorclass=pymysql.cursors.DictCursor  # 游标返回字典格式（便于取值）
                )
            # elif db_type == "oracle":
            #     # 连接Oracle（需要安装cx_Oracle，配置Oracle客户端）
            #     dsn = cx_Oracle.makedsn(
            #         host=self.current_db_config["host"],
            #         port=self.current_db_config["port"],
            #         service_name=self.current_db_config["service_name"]
            #     )
            #     self.conn = cx_Oracle.connect(
            #         user=self.current_db_config["user"],
            #         password=self.current_db_config["password"],
            #         dsn=dsn,
            #         encoding="utf-8",
            #         nencoding="utf-8"
            #     )
            #     self.cursor = self.conn.cursor()
            # elif db_type == "postgresql":
            #     # 连接PostgreSQL
            #     self.conn = psycopg2.connect(
            #         host=self.current_db_config["host"],
            #         port=self.current_db_config["port"],
            #         user=self.current_db_config["user"],
            #         password=self.current_db_config["password"],
            #         dbname=self.current_db_config["database"],
            #         connect_timeout=self.current_db_config["connect_timeout"]
            #     )
            #     self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            else:
                raise DatabaseError(f"不支持的数据库类型：{db_type}（支持：mysql、oracle、postgresql）")

            # 创建游标（MySQL单独处理，其他数据库在对应分支创建）
            if db_type == "mysql":
                self.cursor = self.conn.cursor()
            log.info(f"✅ 成功连接数据库：{db_type}，数据库：{self.current_db_config['database']}")
        except Exception as e:
            raise DatabaseError(f"数据库连接失败：{str(e)}")

    def execute_sql(self, sql: str, params: tuple = None):
        """
        执行SQL语句（通用方法，支持查询、新增、修改、删除）
        :param sql: SQL语句
        :param params: SQL参数（避免SQL注入，如 (1, "test")）
        :return: 执行结果（查询返回结果列表，其他操作返回影响行数）
        """
        try:
            log.info(f"执行SQL语句：{sql}，参数：{params}")
            # 执行SQL
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            # 判断SQL类型（查询类SQL返回结果，其他返回影响行数）
            sql_type = sql.strip().upper().split()[0]
            if sql_type in ["SELECT", "DESCRIBE", "SHOW"]:
                # 查询类SQL，返回结果列表（字典格式）
                result = self.cursor.fetchall()
                log.info(f"SQL查询结果：{result}，共{len(result)}条数据")
                return result
            else:
                # 新增/修改/删除，提交事务，返回影响行数
                self.conn.commit()
                affected_rows = self.cursor.rowcount
                log.info(f"SQL执行成功，影响行数：{affected_rows}")
                return affected_rows
        except Exception as e:
            # 执行失败，回滚事务
            self.conn.rollback()
            raise DatabaseError(f"SQL执行失败：{str(e)}，SQL：{sql}，参数：{params}")

    def query_one(self, sql: str, params: tuple = None):
        """
        查询单条数据（简化查询，返回第一条结果）
        :param sql: 查询SQL
        :param params: SQL参数
        :return: 单条结果（字典格式，无结果返回None）
        """
        result = self.execute_sql(sql, params)
        return result[0] if result else None

    def query_scalar(self, sql: str, params: tuple = None):
        """
        查询单个值（如 COUNT(*)、MAX(id)）
        :param sql: 查询SQL
        :param params: SQL参数
        :return: 单个值（无结果返回None）
        """
        result = self.execute_sql(sql, params)
        return result[0][0] if result else None

    def close(self):
        """关闭数据库连接（释放资源）"""
        if self.cursor:
            self.cursor.close()
            log.info("数据库游标已关闭")
        if self.conn:
            self.conn.close()
            log.info("数据库连接已关闭")


# 导出全局DbClient实例（单例模式）
db_client = DbClient()
