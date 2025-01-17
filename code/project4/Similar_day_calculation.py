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

    # 获取数据
    result = fetch_data(url, data)
    print(len(result))
    if result:
        try:
            # 定义变量与 result 索引的映射
            variables = {
                "out_temp": "JiFang1/SimilarDay/OUT_T",
                "JiFang9_BHSB_EC1_Run":"JiFang9/BHSB_EC1/Run",
                "JiFang9_BHSB_EC2_Run": "JiFang9/BHSB_EC2/Run",
                "JiFang9_BHSB_EC3_Run": "JiFang9/BHSB_EC3/Run",
                "JiFang9_BHSB_EC4_Run": "JiFang9/BHSB_EC4/Run",
                "JiFang30_BHSB_EC1_Run": "JiFang30/BHSB_EC1/Run",
                "JiFang30_BHSB_EC2_Run": "JiFang30/BHSB_EC2/Run",
                "JiFang30_BHSB_EC3_Run": "JiFang30/BHSB_EC3/Run",
                "air_supply_temp": "JiFang1/SimilarDay/LDGS_T",
                "water_inlet_temp": "JiFang1/SimilarDay/LQHS_T",
                "cooling_capacity_kwh": "JiFang1/LenLiangZ",
                "energy_consumption_kwh": "JiFang1/XTZ_KWH",
                "cooling_price":"JiFang1/LL_Price"
            }

            # 遍历变量字典，逐一赋值
            for index_data in result:
                for key, value in variables.items():
                    if value == index_data['tagName'] and len(index_data['values'])>0:
                        compare_data_list[key] = index_data["values"]
            for key ,value in variables.items():
                if key not in compare_data_list:
                    compare_data_list[key] = []
                    for i in result[0]['values']:
                        compare_data_list[key].append({'t':i['t'],'v':0,'s':1})
            # 验证数据范围
            compare_data_list = validate_data_in_range(compare_data_list)

            # 获取时间范围并生成日期列表
            start_time = data.get('start')
            end_time = data.get('end')

            if not start_time or not end_time:
                raise Exception("Missing 'start' or 'end' in input data.")

            try:
                start = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                end = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            except ValueError as e:
                raise Exception(f"Invalid date format for 'start' or 'end': {e}")

            date_list = []
            current_date = start
            while current_date <= end:
                date_list.append(current_date.strftime("%Y-%m-%d"))
                current_date += timedelta(days=1)

            compare_data_list["time_list"] = date_list
            return compare_data_list

        except Exception as e:
            print(f"Error processing data: {e}")
            raise  # 向外层抛出异常以供进一步处理
    else:
        raise Exception("数据获取失败")


def fetch_history_data2(url, data):
    compare_data_list = {}
    result = fetch_data(url, data)
    print(len(result))
    if result:
        try:
            # 定义变量与 result 索引的映射
            variables = {
                "supply_temp": 0,
                "return_temp": 1,
                "src_in_temp": 2,
                "src_out_temp": 3,
                "out_temp": 4,
                "out_humidity": 5,
                "out_wetbulb": 6,
                "FreFB1": 7,
                "FreFB2": 8,
                "Pump_run1": 9,
                "Pump_run2": 10,
                "ZLJ1_COP": 11,
                "ZLJ2_COP": 12,
                "ZLJ1_SSLengLiang": 13,
                "ZLJ2_SSLengLiang": 14,
                "ZLJ1_KW": 15,
                "ZLJ2_KW": 16,
                "ZLJ_Now_Load1": 17,
                "ZLJ_Now_Load2": 18,
                "total_power": 19,
                "cooling_capacity": 20,
                "total_energy": 21,
                "cooling_price": 22,
            }

            # 遍历变量字典，逐一赋值
            for key, index in variables.items():
                try:
                    compare_data_list[key] = result[index]["values"]
                except (IndexError, KeyError) as e:
                    print(f"Warning: Missing or invalid data for '{key}': {e}")
                    compare_data_list[key] = []  # 设置默认值为空列表

            # 验证数据范围
            compare_data_list = validate_data_in_range2(compare_data_list)

            return compare_data_list

        except Exception as e:
            print(f"Error while processing result data: {e}")
            return {}
    else:
        raise Exception("数据获取失败")


def fetch_history_data3(url, data):
    compare_data_list = {}
    result = fetch_data(url, data)
    print(result)
    print(len(result))
    if result:
        try:
            compare_data_list["cooling_capacity"] = result[0]["values"]
            # 验证数据范围
            compare_data_list['cooling_capacity'] = validate_value(compare_data_list.get('cooling_capacity', 0), VALID_COOLING_CAPACITY_RANGE)
            return compare_data_list
        except Exception as e:
            print(f"Error while processing result data: {e}")
            return {}
    else:
        raise Exception("数据获取失败")

# ========== 2. 数据验证与处理 ==========
def validate_value(data_list, valid_range):
    for data in data_list:
        if data['v'] < valid_range[0]:
            data['v'] = valid_range[0]  # 返回最小有效值
        elif data['v'] > valid_range[1]:
            data['v'] = valid_range[1]  # 返回最大有效值
    return data_list
def validate_data_in_range(data_list):
    # 对每个数据进行验证和处理
    data_list['out_temp'] = validate_value(data_list['out_temp'], OUT_TEMP)
    data_list['air_supply_temp'] = validate_value(data_list['air_supply_temp'], AIR_SUPPLY_TEMP)
    data_list['water_inlet_temp'] = validate_value(data_list['water_inlet_temp'], WATER_INLET_TEMP)
    data_list['cooling_capacity_kwh'] = validate_value(data_list['cooling_capacity_kwh'], COOLING_CAPACITY_KWH)
    data_list['energy_consumption_kwh'] = validate_value(data_list['energy_consumption_kwh'], ENERGY_CONSUMPTION_KWH)

    return data_list

def validate_data_in_range2(data_list):
    # 对每个数据进行验证和处理
    data_list['supply_temp'] = validate_value(data_list.get('supply_temp', 0), VALID_SUPPLY_TEMP_RANGE)
    data_list['return_temp'] = validate_value(data_list.get('return_temp', 0), VALID_RETURN_TEMP_RANGE)
    data_list['src_in_temp'] = validate_value(data_list.get('src_in_temp', 0), VALID_SRC_IN_TEMP_RANGE)
    data_list['src_out_temp'] = validate_value(data_list.get('src_out_temp', 0), VALID_SRC_OUT_TEMP_RANGE)
    data_list['out_temp'] = validate_value(data_list.get('out_temp', 0), VALID_OUT_TEMP_RANGE)
    data_list['out_humidity'] = validate_value(data_list.get('out_humidity', 0), VALID_OUT_HUMIDITY_RANGE)
    data_list['out_wetbulb'] = validate_value(data_list.get('out_wetbulb', 0), VALID_OUT_WETBULB_RANGE)
    data_list['FreFB1'] = validate_value(data_list.get('FreFB1', 0), VALID_PUMP_FREQ_RANGE)
    data_list['FreFB2'] = validate_value(data_list.get('FreFB2', 0), VALID_PUMP_FREQ_RANGE)
    data_list['ZLJ1_COP'] = validate_value(data_list.get('ZLJ1_COP', 0), VALID_UNIT_DATA_RANGE)
    data_list['ZLJ2_COP'] = validate_value(data_list.get('ZLJ2_COP', 0), VALID_UNIT_DATA_RANGE)
    data_list['ZLJ1_SSLengLiang'] = validate_value(data_list.get('ZLJ1_SSLengLiang', 0), VALID_UNIT_DATA_RANGE)
    data_list['ZLJ2_SSLengLiang'] = validate_value(data_list.get('ZLJ2_SSLengLiang', 0), VALID_UNIT_DATA_RANGE)
    data_list['ZLJ1_KW'] = validate_value(data_list.get('ZLJ1_KW', 0), VALID_UNIT_DATA_RANGE)
    data_list['ZLJ2_KW'] = validate_value(data_list.get('ZLJ2_KW', 0), VALID_UNIT_DATA_RANGE)
    data_list['ZLJ_Now_Load1'] = validate_value(data_list.get('ZLJ_Now_Load1', 0), VALID_UNIT_DATA_RANGE)
    data_list['ZLJ_Now_Load2'] = validate_value(data_list.get('ZLJ_Now_Load2', 0), VALID_UNIT_DATA_RANGE)
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

def calculate_daily_cooling_price(start_time, end_time, records):
    for record in records:
        record_time = datetime.strptime(record["t"], "%Y-%m-%d %H:%M:%S")
        # 找最接近 start_time 的值
        if record_time < start_time or record_time > end_time:
            continue
        return record["v"]

def Altitude_mode_running_time(start_time, end_time, compare_data_list):
    """
    计算满足条件的运行时长。
    条件：
        1. (JiFang9_BHSB_EC1_Run | JiFang9_BHSB_EC2_Run) |
           (JiFang30_BHSB_EC1_Run & JiFang30_BHSB_EC2_Run & JiFang30_BHSB_EC3_Run)
        2. (!JiFang9_BHSB_EC3_Run | !JiFang9_BHSB_EC4_Run) |
           (!JiFang30_BHSB_EC1_Run & !JiFang30_BHSB_EC2_Run & !JiFang30_BHSB_EC3_Run)
    返回：
        字典形式的时长统计结果，包含两组条件的运行时长（单位：秒）。
    """
    # 初始化运行时长
    condition_1_duration = 0
    condition_2_duration = 0

    # 对齐数据按时间排序
    zipped_data = zip(
        compare_data_list['JiFang9_BHSB_EC1_Run'],
        compare_data_list['JiFang9_BHSB_EC2_Run'],
        compare_data_list['JiFang9_BHSB_EC3_Run'],
        compare_data_list['JiFang9_BHSB_EC4_Run'],
        compare_data_list['JiFang30_BHSB_EC1_Run'],
        compare_data_list['JiFang30_BHSB_EC2_Run'],
        compare_data_list['JiFang30_BHSB_EC3_Run'],
    )
    previous_record = None

    for JiFang9_EC1, JiFang9_EC2, JiFang9_EC3, JiFang9_EC4, JiFang30_EC1, JiFang30_EC2, JiFang30_EC3 in zipped_data:
        # 获取当前时间戳
        times = [
            JiFang9_EC1["t"],
            JiFang9_EC2["t"],
            JiFang9_EC3["t"],
            JiFang9_EC4["t"],
            JiFang30_EC1["t"],
            JiFang30_EC2["t"],
            JiFang30_EC3["t"],
        ]

        # 确保所有时间一致
        if len(set(times)) != 1:
            continue  # 跳过时间不一致的记录

        record_time = datetime.strptime(times[0], "%Y-%m-%d %H:%M:%S")

        # 跳过不在时间范围内的数据
        if record_time < start_time or record_time > end_time:
            continue

        # 如果存在前一条记录，计算时间差
        if previous_record:
            prev_time = datetime.strptime(previous_record["t"], "%Y-%m-%d %H:%M:%S")
            time_delta = (record_time - prev_time).total_seconds()

            # 获取状态值
            JiFang9_EC1_status = JiFang9_EC1["s"]
            JiFang9_EC2_status = JiFang9_EC2["s"]
            JiFang9_EC3_status = JiFang9_EC3["s"]
            JiFang9_EC4_status = JiFang9_EC4["s"]
            JiFang30_EC1_status = JiFang30_EC1["s"]
            JiFang30_EC2_status = JiFang30_EC2["s"]
            JiFang30_EC3_status = JiFang30_EC3["s"]

            # 条件 1 判断
            condition_1 = (
                    (JiFang9_EC1_status != 0 or JiFang9_EC2_status != 0) or
                    (JiFang30_EC1_status != 0 and JiFang30_EC2_status != 0 and JiFang30_EC3_status != 0)
            )
            if condition_1:
                condition_1_duration += time_delta

            # 条件 2 判断
            condition_2 = (
                    (JiFang9_EC3_status == 0 or JiFang9_EC4_status == 0) or
                    (JiFang30_EC1_status == 0 and JiFang30_EC2_status == 0 and JiFang30_EC3_status == 0)
            )
            if condition_2:
                condition_2_duration += time_delta

        # 更新前一条记录
        previous_record = JiFang9_EC1  # 以 JiFang9_BHSB_EC1_Run 为基准记录时间

    # 返回结果
    return {
        "Day_RunTime": condition_1_duration,
        "Night_RunTime": condition_2_duration,
    }

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

        peak_mode_duration = Altitude_mode_running_time(start_time, end_time, compare_data_list)

        cooling_price = calculate_daily_cooling_price(start_time, end_time, compare_data_list['cooling_price'])

        # 添加到结果中
        results.append({
            "date": date,
            "similarity": similarity,
            "min_temp": min_temp,
            "max_temp": max_temp,
            "daytime_avg_temp": daytime_avg_temp,
            "nighttime_avg_temp": nighttime_avg_temp_one + nighttime_avg_temp_two,
            "peak_mode_duration": peak_mode_duration['Day_RunTime'],
            "night_mode_duration": peak_mode_duration['Night_RunTime'],
            "air_supply_temp": air_supply_temp,
            "water_inlet_temp": water_inlet_temp,
            "cooling_capacity_kwh": cooling_capacity_kwh,
            "energy_consumption_kwh": energy_consumption_kwh,
            "cooling_price" :cooling_price
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

    for key, values in grouped.items():
        for time,properties_values in values.items():
            if properties_values['Pump_run1'] ==1 and properties_values['Pump_run2'] ==1:
                properties_values['pump_freq'] = (properties_values['FreFB1'] + properties_values['FreFB2'])/2
            elif properties_values['Pump_run1'] ==1:
                properties_values['pump_freq'] = (properties_values['FreFB1'])
            elif properties_values['Pump_run2'] ==1:
                properties_values['pump_freq'] = (properties_values['FreFB2'])
            else:
                properties_values['pump_freq'] = 0

    return grouped

def predict_remaining_cooling(compare_data_list, today_data_dict, current_time):
    """
    根据相似日冷量曲线预测今天剩余时间的冷量曲线。

    参数:
        compare_data_list (dict): 相似日数据字典，包含 'time_list' 和 'cooling_capacity'。
        today_data_dict (dict): 今日数据字典，包含 'time_list' 和 'cooling_capacity'。
        current_time (datetime): 当前时刻，用于区分今日已过去时间和剩余时间。
    返回:
        list: 今日剩余时间的冷量曲线预测值。
    """
    today_data = sorted(today_data_dict["cooling_capacity"], key=lambda x: x["t"])
    similar_day_data = sorted(compare_data_list["cooling_capacity"], key=lambda x: x["t"])
    predicted_today_data = []
    difference = 0

    for today_point,similar_point in zip(today_data,similar_day_data):
        today_time = datetime.strptime(today_point["t"].split(" ")[1], "%H:%M:%S")
        if today_time <= current_time:
            predicted_today_data.append({"t": today_point["t"], "v": today_point["v"]})

        difference += similar_point["v"] - today_point["v"]

    difference = round(difference/len(today_data),2)

    for i,similar_point in enumerate(similar_day_data):
        similar_time = similar_point["t"].split(" ")[1]
        formatted_current_time = str(current_time.strftime("%Y-%m-%d %H:%M:%S")).split(" ")[1]
        # 当前时间之前的数据保持不变
        if similar_time <= formatted_current_time:
            continue

        current_similar_value = similar_point["v"]
        if difference > 0:
            predicted_value = current_similar_value - difference
        else:
            predicted_value = current_similar_value + difference

        predicted_today_data.append({"t": similar_point["t"], "v": predicted_value})

    return predicted_today_data


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

# ========== 8. 主逻辑(负荷预测 ) ==========
@app.route("/Load_forecasting", methods=['POST'])
def Load_forecasting():
    # 获取历史数据
    try:
        now = datetime.now()
        request_data = request.json
        url = request_data['url']  # 获取 URL
        data_compare = request_data['similar_data']  # 获取 data_compare
        data = request_data['data']  # 获取 data
        compare_data_list = fetch_history_data3(url, data_compare)
        today_data_dict = fetch_history_data3(url, data)

        res_values = predict_remaining_cooling(compare_data_list, today_data_dict,now)
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 400

    return jsonify(res_values), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=1820, debug=True)
