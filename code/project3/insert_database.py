import pymysql
from datetime import date, timedelta

# MySQL 数据库配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'dcny123',
    'database': 'audit'
}

try:
    # 连接 MySQL 数据库
    source_conn = pymysql.connect(**DB_CONFIG)
    source_cursor = source_conn.cursor()

    # 定义起始日期和结束日期
    start_date = date(2025, 1, 1)
    end_date = date(2025, 2, 1)

    # 循环插入日期和状态
    current_date = start_date
    while current_date < end_date:
        # 判断是否是工作日（周一到周五为工作日，周六周日为休息日）
        is_weekend = current_date.weekday() >= 5  # weekday()返回0~6，周六周日为5和6
        holiday_status = 0 if is_weekend else 1  # 0表示休息日，1表示工作日

        # 插入数据，使用 ON DUPLICATE KEY UPDATE 避免重复插入
        insert_query = """
        INSERT INTO schedule (datetime, holiday)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE holiday = VALUES(holiday)
        """
        source_cursor.execute(insert_query, (current_date, holiday_status))

        # 日期加1天
        current_date += timedelta(days=1)

    # 提交事务
    source_conn.commit()

    print("数据插入完成！")

except pymysql.MySQLError as e:
    print(f"数据库操作失败：{e}")
finally:
    # 关闭数据库连接
    if source_cursor:
        source_cursor.close()
    if source_conn:
        source_conn.close()
