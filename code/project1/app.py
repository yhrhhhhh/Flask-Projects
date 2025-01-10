from flask import Flask, request,jsonify
from pydantic import BaseModel, validator, ValidationError
from typing import List
from datetime import datetime, timedelta
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app, supports_credentials=True)
class ValueItem(BaseModel):
    v: float  # 浮动值
    s: int    # 状态值
    t: str    # 时间字符串

    # 时间格式验证
    @validator('t')
    def validate_time_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M:%S")  # 验证时间格式
        except ValueError:
            raise ValueError(f"Invalid datetime format: {v}")
        return v

class SensorData(BaseModel):
    tagName: str  # 标签名
    vt: int       # 类型
    values: List[ValueItem]  # 数据值列表

    # 校验 values 是否为空
    @validator('values')
    def validate_values(cls, v):
        if not v:
            raise ValueError("The 'values' list cannot be empty")
        return v

    # 时间递增性校验
    @validator('values')
    def validate_time_increasing(cls, v):
        last_time = None
        for item in v:
            current_time = datetime.strptime(item.t, "%Y-%m-%d %H:%M:%S")
            if last_time and current_time <= last_time:
                raise ValueError(f"Time must be strictly increasing: {item.t} comes after {last_time}")
            last_time = current_time
        return v
def update_data(existing_data, data, unit):
    # 解析 new_data 中的时间，获取到根据 unit 对齐的时间
    new_data = data['values']
    for item in new_data:
        # 解析时间
        new_time = datetime.strptime(item['t'], "%Y-%m-%d %H:%M:%S")

        # 计算根据 unit 对齐的时间
        new_time_unit = new_time.replace(minute=0, second=0, microsecond=0)  # 设置为小时的开始时间
        # 以 unit 为单位对齐时间
        delta = (new_time - new_time_unit).total_seconds()
        aligned_time = new_time_unit + timedelta(seconds=(delta // unit) * unit)

        flag = 0
        # 查找是否已有该时间的数据，如果没有则新增
        for entry in existing_data:
            existing_time = datetime.strptime(entry["time"], "%Y-%m-%d %H:%M:%S")
            if existing_time == aligned_time:
                if data["tagName"] in entry.keys():
                    break
                # 如果时间匹配，更新对应的 tagName 值
                entry[data["tagName"]] = item["v"]
                flag = 1
                break

        if flag == 0:
            # 如果没有找到匹配的时间，创建新记录
            new_entry = {
                "time": aligned_time.strftime("%Y-%m-%d %H:%M:%S"),
                data["tagName"]: item["v"]
            }
            existing_data.append(new_entry)

    return existing_data

def Complete_data_start(start_time_str, data, unit):
    start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")

    # 获取所有的时间点
    times = [entry["time"] for entry in data]
    times = sorted(set(times))  # 确保时间点唯一并排序

    # 转换时间点为 datetime 对象
    times = [datetime.strptime(time, "%Y-%m-%d %H:%M:%S") for time in times]

    # 创建时间序列（从 start_time 到数据中最后的时间点，按 unit 增加）
    all_times = []
    current_time = start_time
    while current_time <= times[-1]:
        all_times.append(current_time)
        current_time += timedelta(seconds=unit)  # 使用 unit 作为增量

    # 填充数据
    filled_data = []
    for t in all_times:
        # 如果该时间点的数据存在，直接加入
        data_at_time = next((entry for entry in data if datetime.strptime(entry["time"], "%Y-%m-%d %H:%M:%S") == t),
                            None)

        if data_at_time:
            filled_data.append(data_at_time)
        else:
            # 找到下一个时间点的数据进行填充
            next_data = next((entry for entry in data if datetime.strptime(entry["time"], "%Y-%m-%d %H:%M:%S") > t),
                             None)

            if next_data:
                # 用下一个时间点的数据填充当前时间点
                filled_entry = {"time": t.strftime("%Y-%m-%d %H:%M:%S")}
                for key in next_data:
                    if key != "time":
                        filled_entry[key] = next_data[key]
                filled_data.append(filled_entry)

    # 输出结果
    return filled_data

def Complete_data_end(start_time_str, end_time_str, data, unit):
    start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")

    # 获取所有的时间点
    times = [entry["time"] for entry in data]
    times = sorted(set(times))  # 确保时间点唯一并排序

    # 转换时间点为 datetime 对象
    times = [datetime.strptime(time, "%Y-%m-%d %H:%M:%S") for time in times]

    # 创建时间序列（从 start_time 到 end_time，按 unit 增加）
    all_times = []
    current_time = start_time
    while current_time <= end_time:
        all_times.append(current_time)
        current_time += timedelta(seconds=unit)
    # 填充数据
    filled_data = []
    last_data = None  # 用于存储最后一个有效的数据

    for t in all_times:
        # 查找当前时间点的数据
        data_at_time = next((entry for entry in data if datetime.strptime(entry["time"], "%Y-%m-%d %H:%M:%S") == t), None)

        if data_at_time:
            # 当前时间点有数据，直接使用
            filled_data.append(data_at_time)
            last_data = data_at_time
        else:
            if last_data:
                # 如果当前时间点没有数据，使用最后的数据进行填充
                filled_entry = {"time": t.strftime("%Y-%m-%d %H:%M:%S")}
                for key in last_data:
                    if key != "time":
                        filled_entry[key] = last_data[key]
                filled_data.append(filled_entry)

    # 输出结果
    return filled_data

# 保存数据到 JSON 文件的函数
def save_to_json(data, filename="res.json"):
    current_directory = os.path.dirname(__file__)
    file_path = os.path.join(current_directory, filename)

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    print(f"Data has been saved to {file_path}")


# 单独的时间递增性验证函数
def validate_time_increasing_field(v: List[ValueItem]):
    last_time = None
    for item in v:
        # 确保时间解析正确
        try:
            current_time = datetime.strptime(item.t, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError(f"Invalid datetime format: {item.t}")

        # 非严格递增性检查，允许时间点相同
        if last_time and current_time < last_time:
            raise ValueError(
                f"Time must be non-decreasing: {item.t} comes before {last_time}")
        last_time = current_time
    return v

# 示例模型
class SensorData2(BaseModel):
    data: List[ValueItem]

    # 在模型内部进行验证
    @classmethod
    def validate_time_increasing(cls, v: List[ValueItem]):
        return validate_time_increasing_field(v)

def format_timedelta(timedelta_obj):
    total_seconds = int(timedelta_obj.total_seconds())  # 获取总秒数
    hours = total_seconds // 3600  # 计算小时
    minutes = (total_seconds % 3600) // 60  # 计算分钟
    seconds = total_seconds % 60  # 计算秒数
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def calculate_cumulative_time(fh, mh, oh, setData1, setData2, setData3):
    # 将所有数据归类为 (time, value, source)
    all_data = []
    for entry in fh or []:
        all_data.append({"time": entry["t"], "v": entry["v"], "source": "fh"})
    for entry in mh or []:
        all_data.append({"time": entry["t"], "v": entry["v"], "source": "mh"})
    for entry in oh or []:
        all_data.append({"time": entry["t"], "v": entry["v"], "source": "oh"})

    # 按时间排序
    all_data.sort(key=lambda x: datetime.strptime(x["time"], "%Y-%m-%d %H:%M:%S"))

    # 累计匹配的时间
    total_time = timedelta(0)
    last_matched_time = None
    in_matching_period = False

    def is_value_matching(time, source):
        """检查某个时间点的值是否匹配设定值"""
        matching_value = {"fh": setData1, "mh": setData2, "oh": setData3}[source]
        # 先找到时间点最接近的上下边界
        filtered_data = [d for d in all_data if d["source"] == source]
        for i, entry in enumerate(filtered_data):
            current_time = datetime.strptime(entry["time"], "%Y-%m-%d %H:%M:%S")
            if current_time == time:
                return entry["v"] == matching_value
            elif current_time > time:
                if i == 0:
                    return False
                prev_entry = filtered_data[i - 1]
                prev_time = datetime.strptime(prev_entry["time"], "%Y-%m-%d %H:%M:%S")
                # 时间区间判断
                return (
                    prev_entry["v"] == matching_value
                    and entry["v"] == matching_value
                    and prev_time <= time <= current_time
                )
        return False  # 未找到匹配的时间点

    # 遍历所有时间点
    for entry in all_data:
        current_time = datetime.strptime(entry["time"], "%Y-%m-%d %H:%M:%S")

        # 检查 fh, mh, oh 是否匹配
        fh_match = is_value_matching(current_time, "fh") if fh else True
        mh_match = is_value_matching(current_time, "mh") if mh else True
        oh_match = is_value_matching(current_time, "oh") if oh else True

        if fh_match and mh_match and oh_match:
            if not in_matching_period:
                # 开始新的匹配周期
                last_matched_time = current_time
                in_matching_period = True
        else:
            if in_matching_period and last_matched_time:
                # 结束匹配周期，计算时间差
                total_time += current_time - last_matched_time
                in_matching_period = False

    # 如果最后一个周期未结束，补充计算时间
    if in_matching_period and last_matched_time:
        last_time = datetime.strptime(all_data[-1]["time"], "%Y-%m-%d %H:%M:%S")
        total_time += last_time - last_matched_time

    return format_timedelta(total_time)

@app.route("/flask", methods=['POST'])
def align_and_update_data():
    data = request.json  # 获取请求数据

    res_list = []  # 初始化结果列表
    validation_errors = []  # 用于收集验证错误

    for json_data in data['data']:
        try:
            # 尝试使用 SensorData 验证数据
            sensor_data = SensorData(**json_data)
            print("Data is valid!")
            # 如果数据有效，调用更新函数
            res_list = update_data(res_list, json_data, data['unit'])
        except ValidationError as e:
            # 捕获 Pydantic 验证错误并记录
            validation_errors.append({
                'error': 'ValidationError',
                'details': e.errors()  # 使用 .errors() 获取详细的错误信息
            })
            print(f"Validation failed for data: {json_data}")
            print(e.json())  # 打印详细的验证错误信息
            continue  # 继续处理下一个数据项

    # 如果有验证错误，返回错误响应
    if validation_errors:
        return jsonify({
            "status": "error",
            "message": "Validation failed for some data",
            "errors": validation_errors
        }), 400  # 返回 400 Bad Request

    # 数据处理完毕后，执行数据补充
    res_list = Complete_data_start(data["starttime"], res_list, data['unit'])
    res_list = Complete_data_end(data["starttime"], data["endtime"], res_list, data['unit'])

    print(res_list)  # 打印最终结果
    # 返回成功响应
    return jsonify(res_list), 200, {"Content-Type": "application/json"}

@app.route("/flask2", methods=['POST'])
def match_calculate_cumulative_time():
    data = request.json

    res_list = []
    try:
        for json_data in data['hist']:
            if 'mh' not in json_data.keys() or data["m"] == None:
                json_data['mh'] = []
            else:
                sensor_data = SensorData2(data=json_data['mh'])
                print("Data is valid!")
            if 'fh' not in json_data.keys() or data["f"] == None:
                json_data['fh'] = []
            else:
                sensor_data = SensorData2(data=json_data['mh'])
                print("Data is valid!")
            if 'oh' not in json_data.keys():
                json_data['oh'] = []
            else:
                sensor_data = SensorData2(data=json_data['oh'])
                print("Data is valid!")
            cumulative_time = calculate_cumulative_time(json_data['fh'], json_data['mh'], json_data['oh'], data["f"], data["m"], 1)
            res_list.append(cumulative_time)
            print(res_list)
            print("Data is valid!")
            return json.dumps(res_list), 200, {"Content-Type": "application/json"}
    except ValidationError as e:
        print(e.json())  # 打印详细的验证错误信息
        # 调用函数
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1820, debug=True)
