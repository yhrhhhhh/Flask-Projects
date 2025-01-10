import os
import json
import numpy as np
from sklearn.svm import SVR
from scipy.spatial.distance import cdist
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import joblib
import requests
import schedule
import matplotlib
from flask_cors import CORS
from flask import Flask, request,jsonify,abort

matplotlib.use('TkAgg')  # 更改为 TkAgg 后端

app = Flask(__name__)
CORS(app, supports_credentials=True)

# 文件路径常量
MODEL_FILE = "cop_model.pkl"
CACHE_FILE = "cop_history_cache.json"

# 数据范围定义（请根据实际情况调整）
VALID_LOAD_LEVEL_RANGE = (0, 100)  # 负荷率范围：0% 到 100%
VALID_COOLING_TEMP_RANGE = (0, 15)  # 冷却水温度范围：0°C 到 15°C
VALID_FREEZING_TEMP_RANGE = (-10, 10)  # 冷冻水温度范围：-10°C 到 10°C
VALID_COP_RANGE = (2.0, 6.0)  # COP 范围：通常在 2 到 6 之间

#向量回归模型(SVR)参数
C = 30
GAMMA = 0.01

# ========== 1. 数据获取与缓存机制 ==========

def fetch_data(url, data):
    """通用 HTTP POST 请求方法"""
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print(data)
            return response.json()
        else:
            print(f"接口请求失败，状态码：{response.status_code}")
            return None
    except Exception as e:
        print(f"接口请求异常：{e}")
        return None

def fetch_history_data(url, data):
    """获取历史数据并缓存"""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
            print("从缓存加载历史数据")
            return (
                np.array(cache["x_data"]),
                np.array(cache["y_data"]),
                np.array(cache["z_data"]),
                np.array(cache["cop_data"]),
            )

    result = fetch_data(url, data)
    if result:
        x_data = np.array([item["v"] for item in result[1]["values"]])
        y_data = np.array([item["v"] for item in result[2]["values"]])
        z_data = np.array([item["v"] for item in result[3]["values"]])
        cop_data = np.array([item["v"] for item in result[0]["values"]])
        print(x_data)
        # 缓存数据
        with open(CACHE_FILE, "w") as f:
            json.dump({"x_data": x_data.tolist(), "y_data": y_data.tolist(), "z_data": z_data.tolist(), "cop_data": cop_data.tolist()}, f)
        print("已缓存历史数据")
        return x_data, y_data, z_data ,cop_data
    else:
        raise Exception("历史数据获取失败")


# ========== 2. 数据验证与处理 ==========

def validate_data_in_range(x_data, y_data, z_data, cop_data):
    """验证数据是否在合理范围内"""
    # 负荷率、冷却水温度、冷冻水温度、COP 是否超出范围
    valid_data_indices = []

    for i in range(len(x_data)):
        load_level = x_data[i]
        cooling_temp = y_data[i]
        freezing_temp = z_data[i]
        cop = cop_data[i]

        # 检查是否超出负荷率、冷却水温度、冷冻水温度和COP的范围
        if (VALID_LOAD_LEVEL_RANGE[0] <= load_level <= VALID_LOAD_LEVEL_RANGE[1] and
                VALID_COOLING_TEMP_RANGE[0] <= cooling_temp <= VALID_COOLING_TEMP_RANGE[1] and
                VALID_FREEZING_TEMP_RANGE[0] <= freezing_temp <= VALID_FREEZING_TEMP_RANGE[1] and
                VALID_COP_RANGE[0] <= cop <= VALID_COP_RANGE[1]):
            valid_data_indices.append(i)

    print(f"有效数据数量：{len(valid_data_indices)} / {len(x_data)}")
    return valid_data_indices

# ========== 3. 模型训练与预测 ==========

def save_model(model, filepath=MODEL_FILE):
    """保存模型到文件"""
    joblib.dump(model, filepath)

def load_model(filepath=MODEL_FILE):
    """从文件加载模型"""
    if os.path.exists(filepath):
        return joblib.load(filepath)
    return None

def train_model(x_data, y_data, z_data, cop_data):
    """训练 SVR 模型"""
    # 将负荷率、合成温度特征堆叠为一个输入数组
    X = np.vstack((x_data, y_data, z_data)).T
    model = SVR(kernel="rbf", C=C, gamma=GAMMA)
    model.fit(X, cop_data)
    save_model(model)
    print("模型训练完成并保存")
    return model

def calculate_cop_history(x_data, y_data, z_data, model):
    """计算 COP 历史值数组"""
    inputs = np.vstack((x_data, y_data, z_data)).T
    return model.predict(inputs)

# ========== 3. 相似日逻辑 ==========

def find_similar_days(history_data, target_cop=None, similarity_metric="euclidean"):
    """
    找到与目标 COP 值相似的历史日期。
    """
    cop_values = np.array(history_data["cop_data"])
    if target_cop is None:
        target_cop = np.mean(cop_values)
        print(f"未提供 target_cop，默认使用全局平均值：{target_cop}")
    target_cop = np.array(target_cop).reshape(1, -1)
    cop_values = cop_values.reshape(-1, 1)
    distances = cdist(target_cop, cop_values, metric=similarity_metric)
    similar_indices = np.argsort(distances[0])[:5]
    print(f"找到相似日索引：{similar_indices}")
    return similar_indices

def optimize_data_with_similar_days(history_data, similar_indices):
    """使用相似日优化数据"""
    x_data = history_data["x_data"][similar_indices]
    y_data = history_data["y_data"][similar_indices]
    z_data = history_data["z_data"][similar_indices]
    cop_data = history_data["cop_data"][similar_indices]
    return x_data, y_data, z_data, cop_data

# ========== 4. 数据可视化 ==========

def create_combined_temperature_feature(cooling_temp, freezing_temp, method="average"):
    """
    合并冷却水温度和冷冻水温度为一个新的特征：平均值或差值。
    """
    if method == "average":
        return (cooling_temp + freezing_temp) / 2
    elif method == "difference":
        return cooling_temp - freezing_temp
    else:
        raise ValueError("方法仅支持 'average' 或 'difference'")

def plot_cop_surface(x_data, cooling_temp_data, freezing_temp_data, cop_data, model, method="average"):
    """绘制 COP 曲面和原始数据点"""
    # 合成温度特征
    combined_temp_data = create_combined_temperature_feature(cooling_temp_data, freezing_temp_data, method)

    # 生成平滑网格
    x = np.linspace(min(x_data), max(x_data), 100)
    y = np.linspace(min(combined_temp_data), max(combined_temp_data), 100)
    X_grid, Y_grid = np.meshgrid(x, y)

    # 计算对应的 COP 预测值
    Z_pred = model.predict(np.c_[X_grid.ravel(), Y_grid.ravel(), np.full_like(X_grid.ravel(), np.mean(freezing_temp_data))]).reshape(X_grid.shape)

    # 归一化 COP_pred 以便映射到颜色空间
    normed_cop_pred = Z_pred / np.max(Z_pred)
    facecolors = plt.cm.viridis(normed_cop_pred)  # 颜色映射

    # 绘制曲面
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(X_grid, Y_grid, Z_pred, rstride=1, cstride=1, facecolors=facecolors, alpha=0.8)

    # 绘制原始数据点
    ax.scatter(x_data, combined_temp_data, cop_data, c=cop_data, cmap='viridis', s=50, label="Data Points", edgecolors='k')

    # 设置标签
    ax.set_xlabel("LoadLevel(%)")
    ax.set_ylabel("Combined Temperature Feature")
    ax.set_zlabel("COP")

    # 添加色条（颜色映射）
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)

    # 显示图形
    plt.show()

# ========== 5. 定时任务与主逻辑 ==========

def update_cop_cache(url, data):
    """定时更新缓存"""
    x_data, y_data, z_data, cop_data = fetch_history_data(url, data)
    model = load_model()
    if model is None:
        model = train_model(x_data, y_data, z_data, cop_data)
    cop_history = calculate_cop_history(x_data, y_data, z_data, model)
    with open(CACHE_FILE, "w") as f:
        json.dump({"x_data": x_data.tolist(), "y_data": y_data.tolist(), "z_data": z_data.tolist(), "cop_data": cop_data.tolist(), "cop_history": cop_history.tolist()}, f)
    print("COP 历史缓存已更新")

def validate_single_input(load_level, temperature, frozen_temp):
    """
    验证单个输入的负荷率、冷却水温度和冷冻水温度是否在合理范围内。
    如果超出范围，返回 False，否则返回 True。
    """
    if not (VALID_LOAD_LEVEL_RANGE[0] <= load_level <= VALID_LOAD_LEVEL_RANGE[1]):
        print(f"负荷率 {load_level}% 超出有效范围 {VALID_LOAD_LEVEL_RANGE}")
        return False
    if not (VALID_COOLING_TEMP_RANGE[0] <= temperature <= VALID_COOLING_TEMP_RANGE[1]):
        print(f"冷却水温度 {temperature}℃ 超出有效范围 {VALID_COOLING_TEMP_RANGE}")
        return False
    if not (VALID_FREEZING_TEMP_RANGE[0] <= frozen_temp <= VALID_FREEZING_TEMP_RANGE[1]):
        print(f"冷冻水温度 {frozen_temp}℃ 超出有效范围 {VALID_FREEZING_TEMP_RANGE}")
        return False
    return True


@app.route("/select_cop", methods=['POST'])
def predict_cop():
    """
    根据输入的负荷率 (load_level)、冷却水温度 (temperature) 和冷冻水温度 (frozen_temp)，
    使用已训练的 SVR 模型预测 COP 值。如果输入数据超出合理范围，则返回 None。
    """
    try:
        req_data = request.json
        load_level = req_data['load_level']  # 获取 load_level
        temperature = req_data['temperature'] # 获取 temperature
        frozen_temp = req_data['frozen_temp']  # 获取 frozen_temp
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    model = load_model()

    # 数据验证
    if not validate_single_input(load_level, temperature, frozen_temp):
        abort(400, description="输入数据无效，无法进行预测。")

    input_data = np.array([[load_level, temperature, frozen_temp]])
    predicted_cop = model.predict(input_data)
    print(f"负荷率：{load_level}%，冷却水温度：{temperature}℃，冷冻水温度：{frozen_temp}℃ 的预测值 COP: {predicted_cop[0]}")
    return json.dumps((predicted_cop)[0]), 200, {"Content-Type": "application/json"}

@app.route("/train_cop_model", methods=['POST'])
def update_and_train_cop_model():
    """主入口函数"""
    # 获取历史数据
    try:
        request_data = request.json
        url = request_data['url']  # 获取 URL
        data = request_data['data']  # 获取 data
        x_data, y_data, z_data, cop_data = fetch_history_data(url, data)  #Todo
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 400

    valid_indices = validate_data_in_range(x_data, y_data, z_data, cop_data)

    # 过滤不合适的数据
    x_data = x_data[valid_indices]
    y_data = y_data[valid_indices]
    z_data = z_data[valid_indices]
    cop_data = cop_data[valid_indices]

    # 加载或训练模型
    model = load_model()
    if model is None:
        model = train_model(x_data, y_data, z_data, cop_data)
    # 查找相似日
    similar_indices = find_similar_days({"x_data": x_data, "y_data": y_data, "z_data": z_data, "cop_data": cop_data})

    # 用相似日数据优化模型
    optimized_x, optimized_y, optimized_z, optimized_cop = optimize_data_with_similar_days(
        {"x_data": x_data, "y_data": y_data, "z_data": z_data, "cop_data": cop_data}, similar_indices
    )

    # 用相似日数据重新训练模型
    model = train_model(optimized_x, optimized_y, optimized_z, optimized_cop)

    # 可视化
    plot_cop_surface(x_data, y_data, z_data, cop_data, model)

    # 定时任务：每小时更新缓存
    schedule.every(1).hours.do(update_cop_cache)
    while True:
        schedule.run_pending()


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=1820, debug=True)
