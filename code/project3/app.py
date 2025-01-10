from flask import Flask, request, jsonify, abort
import pymysql

app = Flask(__name__)

# MySQL 数据库配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'dcny123',
    'database': 'audit'
}


# 连接 MySQL 数据库
def get_db_connection():
	try:
		source_conn = pymysql.connect(**DB_CONFIG)
		return source_conn
	except pymysql.MySQLError as e:
		print(f"数据库连接失败: {e}")
		return None


# ========== 接口1: 查询日期对应的工休状态 ==========

@app.route('/query_work_rest_status', methods=['POST'])
def query_work_rest_status():
	"""查询一组日期对应的工休状态"""
	try:
		# 获取传入的日期列表
		dates = request.json

		if not dates:
			return jsonify({"status": "error", "message": "日期列表不能为空"}), 400
		# 查询工休状态
		source_conn = get_db_connection()
		if source_conn is None:
			return jsonify({"status": "error", "message": "数据库连接失败"}), 500

		source_cursor = source_conn.cursor()
		placeholders = ', '.join(['%s'] * len(dates))
		query = f"SELECT datetime, holiday FROM schedule WHERE datetime IN ({placeholders})"
		source_cursor.execute(query, dates)

		results = source_cursor.fetchall()

		# 返回工休状态列表
		status_list = [{"date": row[0], "status": row[1]} for row in results]
		return jsonify(status_list), 200

	except Exception as e:
		return jsonify({"status": "error", "message": str(e)}), 500

	finally:
		if source_conn:
			source_conn.close()
			source_cursor.close()


# ========== 接口2: 修改日期对应的工休状态 ==========

@app.route('/update_work_rest_status', methods=['POST'])
def update_work_rest_status():
	"""修改一组日期对应的工休状态"""
	try:
		# 获取传入的日期列表和工休状态列表
		request_data = request.json
		dates = request_data['dates']
		statuses = request_data['statuses']

		if not dates or not statuses or len(dates) != len(statuses):
			return jsonify({"status": "error", "message": "日期列表和状态列表不匹配"}), 400

		# 更新工休状态
		connection = get_db_connection()
		if connection is None:
			return jsonify({"status": "error", "message": "数据库连接失败"}), 500

		cursor = connection.cursor()

		updated_dates = []
		for date, status in zip(dates, statuses):
			update_query = """
                INSERT INTO schedule (datetime, holiday)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE holiday = %s
            """
			cursor.execute(update_query, (date, status, status))
			updated_dates.append(date)

		# 提交更新
		connection.commit()

		# 返回修改了的日期列表
		return jsonify({"status": "success", "updated_dates": updated_dates}), 200

	except Exception as e:
		return jsonify({"status": "error", "message": str(e)}), 500

	finally:
		if connection:
			connection.close()


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=1820, debug=True)
