import requests
from flask_cors import CORS
from flask import Flask, request, jsonify, abort
from datetime import datetime, timedelta
import pymysql
from collections import defaultdict

app = Flask(__name__)
CORS(app, supports_credentials=True)

# 数据范围定义
OUT_TEMP = (-20, 45)  # 气温范围：-20°C 到 45°C
AIR_SUPPLY_TEMP = (10, 35)  # 空调供水温度范围：10°C 到 35°C
WATER_INLET_TEMP = (5, 30)  # 水源侧出水温度范围：5°C 到 30°C
COOLING_CAPACITY_KWH = (0, 10000)  # 冷热量范围：0KWH 到 10000KWH
ENERGY_CONSUMPTION_KWH = (0, 10000)  # 能耗范围：0KWH 到 10000KWH


VALID_SUPPLY_TEMP_RANGE = (0, 15)       # 空调供水温度范围：0°C 到 15°C
VALID_RETURN_TEMP_RANGE = (5, 20)       # 空调回水温度范围：5°C 到 20°C
VALID_SRC_IN_TEMP_RANGE = (10, 35)      # 水源侧进水温度范围：10°C 到 35°C
VALID_SRC_OUT_TEMP_RANGE = (5, 30)      # 水源侧出水温度范围：5°C 到 30°C
VALID_OUT_TEMP_RANGE = (-20, 45)        # 室外温度范围：-20°C 到 45°C
VALID_OUT_HUMIDITY_RANGE = (0, 100)     # 室外湿度范围：0% 到 100%
VALID_OUT_WETBULB_RANGE = (-20, 40)     # 室外湿球温度范围：-20°C 到 40°C
VALID_PUMP_FREQ_RANGE = (0, 60)         # 空调泵频率范围：0Hz 到 60Hz
VALID_UNIT_DATA_RANGE = (0, 1)          # 主机数据范围：0 或 1
VALID_TOTAL_POWER_RANGE = (0, 1000)     # 总功率范围：0kW 到 1000kW
VALID_COOLING_CAPACITY_RANGE = (0, 500) # 瞬时冷量范围：0kW 到 500kW
VALID_TOTAL_ENERGY_RANGE = (0, 1e6)     # 当前累计能耗范围：0 到 1,000,000kWh
VALID_COOLING_PRICE_RANGE = (0, 10)     # 冷量单价范围：0 到 10 元/kWh

# ========== 1. 数据获取 ==========

def fetch_data(url, data):
    """通用 HTTP POST 请求方法"""
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"接口请求失败，状态码：{response.status_code}")
            return None
    except Exception as e:
        print(f"接口请求异常：{e}")
        return None

def fetch_history_data(url, data):
    compare_data_list = {}

    result = fetch_data(url, data)
    if result:
        compare_data_list["out_temp"] = result[0]["values"]
        compare_data_list["run_status"] = result[1]["values"]
        compare_data_list["air_supply_temp"] = result[2]["values"]
        compare_data_list["water_inlet_temp"] = result[3]["values"]
        compare_data_list["cooling_capacity_kwh"] = result[4]["values"]
        compare_data_list["energy_consumption_kwh"] = result[5]["values"]

        compare_data_list = validate_data_in_range(compare_data_list)

        start_time = data['start']
        end_time = data['end']

        start = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

        date_list = []
        current_date = start
        while current_date <= end:
            date_list.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)

        compare_data_list["time_list"] = date_list
        return compare_data_list
    else:
        raise Exception("数据获取失败")

def fetch_history_data2(url, data):
    compare_data_list = {}

    result = fetch_data(url, data)
    if result:
        compare_data_list["supply_temp"] = result[0]["values"]
        compare_data_list["return_temp"] = result[1]["values"]
        compare_data_list["src_in_temp"] = result[2]["values"]
        compare_data_list["src_out_temp"] = result[3]["values"]
        compare_data_list["out_temp"] = result[4]["values"]
        compare_data_list["out_humidity"] = result[5]["values"]
        compare_data_list["out_wetbulb"] = result[6]["values"]
        compare_data_list["pump_freq"] = result[7]["values"]
        compare_data_list["unit_data"] = result[8]["values"]
        compare_data_list["total_power"] = result[9]["values"]
        compare_data_list["cooling_capacity"] = result[10]["values"]
        compare_data_list["total_energy"] = result[11]["values"]

        compare_data_list = validate_data_in_range2(compare_data_list)

        return compare_data_list
    else:
        raise Exception("数据获取失败")

# ========== 2. 数据验证与处理 ==========

def validate_data_in_range(data_list):
    # 定义有效范围检查
    def validate_value(data_list, valid_range):
        for data in data_list:
            if data['v'] < valid_range[0]:
                data['v'] = valid_range[0]  # 返回最小有效值
            elif data['v'] > valid_range[1]:
                data['v'] = valid_range[1]  # 返回最大有效值
        return data_list

    # 对每个数据进行验证和处理
    data_list['out_temp'] = validate_value(data_list['out_temp'], OUT_TEMP)
    data_list['air_supply_temp'] = validate_value(data_list['air_supply_temp'], AIR_SUPPLY_TEMP)
    data_list['water_inlet_temp'] = validate_value(data_list['water_inlet_temp'], WATER_INLET_TEMP)
    data_list['cooling_capacity_kwh'] = validate_value(data_list['cooling_capacity_kwh'], COOLING_CAPACITY_KWH)
    data_list['energy_consumption_kwh'] = validate_value(data_list['energy_consumption_kwh'], ENERGY_CONSUMPTION_KWH)

    return data_list

def validate_data_in_range2(data_list):
    # 定义有效范围检查
    def validate_value(data_list, valid_range):
        for data in data_list:
            if data['v'] < valid_range[0]:
                data['v'] = valid_range[0]  # 返回最小有效值
            elif data['v'] > valid_range[1]:
                data['v'] = valid_range[1]  # 返回最大有效值
        return data_list

    # 对每个数据进行验证和处理
    data_list['supply_temp'] = validate_value(data_list.get('supply_temp', 0), VALID_SUPPLY_TEMP_RANGE)
    data_list['return_temp'] = validate_value(data_list.get('return_temp', 0), VALID_RETURN_TEMP_RANGE)
    data_list['src_in_temp'] = validate_value(data_list.get('src_in_temp', 0), VALID_SRC_IN_TEMP_RANGE)
    data_list['src_out_temp'] = validate_value(data_list.get('src_out_temp', 0), VALID_SRC_OUT_TEMP_RANGE)
    data_list['out_temp'] = validate_value(data_list.get('out_temp', 0), VALID_OUT_TEMP_RANGE)
    data_list['out_humidity'] = validate_value(data_list.get('out_humidity', 0), VALID_OUT_HUMIDITY_RANGE)
    data_list['out_wetbulb'] = validate_value(data_list.get('out_wetbulb', 0), VALID_OUT_WETBULB_RANGE)
    data_list['pump_freq'] = validate_value(data_list.get('pump_freq', 0), VALID_PUMP_FREQ_RANGE)
    data_list['unit_data'] = validate_value(data_list.get('unit_data', 0), VALID_UNIT_DATA_RANGE)
    data_list['total_power'] = validate_value(data_list.get('total_power', 0), VALID_TOTAL_POWER_RANGE)
    data_list['cooling_capacity'] = validate_value(data_list.get('cooling_capacity', 0), VALID_COOLING_CAPACITY_RANGE)
    data_list['total_energy'] = validate_value(data_list.get('total_energy', 0), VALID_TOTAL_ENERGY_RANGE)

    return data_list
# ========== 3. 相似日逻辑 ==========
def group_data_by_date(data):
    """
    将数据按日期分组
    :param data: 包含时间戳和值的字典
    :return: 按日期分组的数据字典
    """
    grouped = defaultdict(list)
    for entry in data['out_temp']:
        date = entry['t'][:10]  # 提取日期部分
        grouped[date].append(entry)

    return grouped


def calculate_similarity(today_data, compare_data, today_date, compare_date, is_holiday_today, is_holiday_compare):
    """
    计算两个日期的数据相似度
    :param today_data: 今天的数据列表
    :param compare_data: 比较日期的数据列表
    :param today_date: 今天的日期
    :param compare_date: 比较的日期
    :param is_holiday_today: 今天是否为节假日
    :param is_holiday_compare: 比较日期是否为节假日
    :return: 相似度值
    """
    similarity = 100.0

    def calculate_variance(data1, data2):
        """
        根据整点时间计算温度方差
        """
        # 生成整点时间
        hourly_times = [datetime.strptime(data1[0]['t'], '%Y-%m-%d %H:%M:%S').replace(hour=0, minute=0, second=0) + timedelta(hours=i) for i in range(24)]

        def get_nearest_entry(entries, target_time):
            """
            获取与目标时间最接近的记录
            """
            nearest = min(entries, key=lambda x: abs(datetime.strptime(x['t'], '%Y-%m-%d %H:%M:%S') - target_time))
            return nearest['v']

        today_temps = [get_nearest_entry(data1, t) for t in hourly_times]
        compare_temps = [get_nearest_entry(data2, t) for t in hourly_times]

        temp_differences = [(t1 - t2) ** 2 for t1, t2 in zip(today_temps, compare_temps)]
        variance = sum(temp_differences) / len(temp_differences)

        return variance

    def calculate_day_of_year(date1, date2):
        """
        计算两个日期的年中天数差异
        """
        day_of_year1 = date1.timetuple().tm_yday
        day_of_year2 = date2.timetuple().tm_yday
        return abs(day_of_year1 - day_of_year2)

    def calculate_holiday_difference(is_holiday1, is_holiday2):
        """
        计算节假日差异
        """
        return 20 if is_holiday1 != is_holiday2 else 0

    # 计算整点温度差异的方差

    variance_diff = calculate_variance(today_data, compare_data)

    # 计算日期差异
    today_date_format = datetime.strptime(today_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
    day_diff = calculate_day_of_year(today_date_format, compare_date)

    # 计算节假日差异
    holiday_diff = calculate_holiday_difference(is_holiday_today, is_holiday_compare)

    # 更新相似度
    similarity -= variance_diff * 0.1
    similarity -= day_diff * 0.1
    similarity -= holiday_diff

    return similarity


def calculate_similar_dates(today_data, compare_data_all, today_date, is_holiday_today, holiday_map):
    """
    计算当前日期与所有对比日期的相似度
    :param today_data: 今天的数据字典
    :param compare_data_all: 历史对比数据字典
    :param today_date: 今天的日期
    :param is_holiday_today: 今天是否为节假日
    :param holiday_map: 包含历史日期的节假日信息的字典
    :return: 最相似的5个日期及相似度
    """
    # 按日期分组历史数据
    grouped_data = group_data_by_date(compare_data_all)
    similarities = []

    # 遍历每个分组数据，计算相似度
    for compare_date, compare_data in grouped_data.items():
        is_holiday_compare = holiday_map.get(compare_date, False)  # 获取比较日期的节假日信息
        similarity = calculate_similarity(today_data['out_temp'], compare_data, today_date,
                                          datetime.strptime(compare_date, "%Y-%m-%d"),
                                          is_holiday_today, is_holiday_compare)
        similarities.append((compare_date, similarity))

    # 按相似度排序，返回最高的5个
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:5]


# ========== 4: 查询日期对应的工休状态 ==========

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


def query_work_rest_status(dates):
    """查询一组日期对应的工休状态"""
    try:
        # 获取传入的日期列表
        if not dates:
            print("日期列表不能为空")
        # 查询工休状态
        source_conn = get_db_connection()
        source_cursor = source_conn.cursor()
        placeholders = ', '.join(['%s'] * len(dates))
        query = f"SELECT datetime, holiday FROM schedule WHERE datetime IN ({placeholders})"
        source_cursor.execute(query, dates)

        results = source_cursor.fetchall()

        status_list = {}
        # 返回工休状态列表
        for row in results:
            if row[1] == 1:
                status_list[str(row[0])] = True
            else:
                status_list[str(row[0])] = False
        print(status_list)
        return status_list

    except Exception as e:
        print(f"数据库获取数据失败: {e}")
        return None

    finally:
        if source_conn:
            source_conn.close()
            source_cursor.close()

# ========== 5. 相关属性值计算 ==========
def temp_average_calculation(start_time,end_time,records):
    values = []
    for record in records:
        record_time = datetime.strptime(record["t"], "%Y-%m-%d %H:%M:%S")
        if start_time <= record_time <= end_time:
            values.append(record["v"])
    if len(values) != 0:
        return sum(values) / len(values)
    else:
        return 0

def temp_min_max_calculation(start_time, end_time, records):
    values = []
    for record in records:
        record_time = datetime.strptime(record["t"], "%Y-%m-%d %H:%M:%S")
        if start_time <= record_time <= end_time:
            values.append(record["v"])
    if len(values) != 0:
        return min(values), max(values)  # 返回最小值和最大值
    else:
        return None, None  # 如果没有值，返回 None

def calculate_daily_difference(start_time, end_time, records):
    closest_start = None
    closest_end = None
    min_start_diff = float("inf")
    min_end_diff = float("inf")

    for record in records:
        record_time = datetime.strptime(record["t"], "%Y-%m-%d %H:%M:%S")
        time_diff_start = abs((record_time - start_time).total_seconds())
        time_diff_end = abs((record_time - end_time).total_seconds())

        # 找最接近 start_time 的值
        if time_diff_start < min_start_diff:
            closest_start = record["v"]
            min_start_diff = time_diff_start

        # 找最接近 end_time 的值
        if time_diff_end < min_end_diff:
            closest_end = record["v"]
            min_end_diff = time_diff_end

    if closest_start is not None and closest_end is not None:
        return closest_end - closest_start
    else:
        raise ValueError("记录为空或未找到任何时间点的值")

def calculate_running_duration(start_time, end_time, records):
    """
    计算在指定时间范围内的运行时长。
    规则：如果记录中时间间隔两边的数据值都为 1，则认为该时间段内都在运行。

    返回：
        运行时长（单位：秒）
    """
    records = sorted(records, key=lambda x: datetime.strptime(x["t"], "%Y-%m-%d %H:%M:%S"))
    running_duration = 0
    previous_record = None

    for record in records:
        record_time = datetime.strptime(record["t"], "%Y-%m-%d %H:%M:%S")

        # 跳过不在范围内的记录
        if record_time < start_time or record_time > end_time:
            continue

        if previous_record is not None:
            prev_time = datetime.strptime(previous_record["t"], "%Y-%m-%d %H:%M:%S")
            prev_status = previous_record["s"]
            current_status = record["s"]

            # 如果时间段两边的状态值都为 1，则累加时间间隔
            if prev_status == 1 and current_status == 1:
                running_duration += (record_time - prev_time).total_seconds()

        # 更新前一个记录为当前记录
        previous_record = record

    return running_duration

def Related_attribute_value_calculation(compare_data_list,top_similar_dates):
    results = []

    for date, similarity in top_similar_dates:
        # 当前日期对应的时间范围
        current_date = datetime.strptime(date, "%Y-%m-%d")
        start_time = current_date
        end_time = current_date.replace(hour=23, minute=59, second=59)
        air_supply_temp = temp_average_calculation(start_time, end_time, compare_data_list['air_supply_temp'])
        water_inlet_temp = temp_average_calculation(start_time, end_time, compare_data_list['water_inlet_temp'])

        daytime_start_time = current_date.replace(hour=8, minute=0, second=0)
        daytime_end_time = current_date.replace(hour=17, minute=59, second=59)

        daytime_avg_temp = temp_average_calculation(daytime_start_time, daytime_end_time, compare_data_list['out_temp'])
        nighttime_avg_temp_one = temp_average_calculation(current_date, daytime_start_time,compare_data_list['out_temp'])
        nighttime_avg_temp_two = temp_average_calculation(daytime_end_time, end_time,compare_data_list['out_temp'])
        min_temp, max_temp = temp_min_max_calculation(start_time, end_time, compare_data_list['out_temp'])

        cooling_capacity_kwh = calculate_daily_difference(start_time, end_time, compare_data_list['cooling_capacity_kwh'])
        energy_consumption_kwh = calculate_daily_difference(start_time, end_time,compare_data_list['energy_consumption_kwh'])

        peak_mode_duration = calculate_running_duration(daytime_start_time, daytime_end_time, compare_data_list['run_status'])
        night_mode_duration_one = calculate_running_duration(current_date, daytime_start_time, compare_data_list['run_status'])
        night_mode_duration_two = calculate_running_duration(daytime_end_time, end_time, compare_data_list['run_status'])


        # 添加到结果中
        results.append({
            "date": date,
            "similarity": similarity,
            "min_temp": min_temp,
            "max_temp": max_temp,
            "daytime_avg_temp": daytime_avg_temp,
            "nighttime_avg_temp": nighttime_avg_temp_one + nighttime_avg_temp_two,
            "peak_mode_duration": peak_mode_duration,
            "night_mode_duration": night_mode_duration_one+night_mode_duration_two,
            "air_supply_temp": air_supply_temp,
            "water_inlet_temp": water_inlet_temp,
            "cooling_capacity_kwh": cooling_capacity_kwh,
            "energy_consumption_kwh": energy_consumption_kwh,
        })

    return results

def Integrated_time_dictionary(data_list):
    """
    将数据按日期分组
    :param data: 包含时间戳和值的字典
    :return: 按日期分组的数据字典
    """
    grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    for key, values in data_list.items():
        for entry in values:
            date = entry['t'][:10]
            date_time = entry['t']  # 提取日期部分
            grouped[date][date_time][key] = entry['v']
    return grouped

# ========== 6. 主逻辑(相似日工况报表) ==========
@app.route("/similar_day_calculation", methods=['POST'])
def Similar_day_calculation():
    """主入口函数"""
    # 获取历史数据
    try:
        request_data = request.json
        url = request_data['url']  # 获取 URL
        data_compare = request_data['data_compare']  # 获取 data_compare
        data = request_data['data']  # 获取 data
        compare_data_list = fetch_history_data(url, data_compare)
        today_data_dict = fetch_history_data(url, data)
        compare_dates = compare_data_list['time_list']
        holidays_compare = query_work_rest_status(compare_dates)
        today_date = today_data_dict['time_list']
        holidays_today = query_work_rest_status(today_date)
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 400
    # 查找相似日
    top_similar_dates = calculate_similar_dates(today_data_dict, compare_data_list, today_date[0],next(iter(holidays_today.values())), holidays_compare)
    variables = Related_attribute_value_calculation(compare_data_list, top_similar_dates)

    similar_dates = [date[0] for date in top_similar_dates]

    return jsonify(variables), 200


# ========== 7. 主逻辑(相似日工况曲线) ==========
@app.route("/Operating_conditions_curve", methods=['POST'])
def Similar_daily_operating_conditions_curve():
    # 获取历史数据
    try:
        request_data = request.json
        url = request_data['url']  # 获取 URL
        data_compare = request_data['data_compare']  # 获取 data_compare
        data = request_data['data']  # 获取 data
        similar_dates = request_data['similar_dates']  # 获取 similar_dates
        compare_data_list = fetch_history_data2(url, data_compare)
        today_data_dict = fetch_history_data2(url, data)

        compare_data = Integrated_time_dictionary(compare_data_list)
        today_data = Integrated_time_dictionary(today_data_dict)

        res_values = today_data
        for time in similar_dates:
            res_values[time] = compare_data[time]

    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 400

    return jsonify(res_values), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=1820, debug=True)
