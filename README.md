# Flask-Projects

### 说明文档：Flask API 应用

### (一)project1:Verify the incoming data format and time incrementability && Calculate accumulated time based on incoming data

#### 项目概述：

该Flask 应用提供以下主要的 POST 请求接口：`/flask` 和 `/flask2`。它们用于处理传入的传感器数据并执行以下操作：

1. **数据校验**：验证传入的数据格式、时间递增性以及必填字段。
2. **数据更新**：根据输入的时间和单位，对数据进行对齐与更新。
3. **时间累计计算**：根据传感器数据计算时间累计。

#### 依赖库：

- `Flask`: 用于创建和管理 Web 应用。
- `Flask-CORS`: 允许跨域请求。
- `Pydantic`: 用于数据验证和解析。
- `datetime`: 处理时间数据。
- `json`: 处理 JSON 数据的输入和输出。
- `os`: 文件路径处理。

### 代码结构：

1. **SensorData 数据模型**：

   - `SensorData` 类用于接收传感器数据，包含标签名称、类型以及数据值列表。
   - `ValueItem` 类代表数据项，每个数据项包括值、状态和时间字段。
   - 使用 `Pydantic` 的 `BaseModel` 实现数据校验。
   - `validate_time_format` 校验时间字段的格式。
   - `validate_time_increasing` 校验时间字段是否严格递增。
   - `validate_non_empty` 校验数据列表是否为空。

2. **数据处理函数**：

   - `update_data(existing_data, data, unit)`: 用于更新数据。如果数据时间已存在则更新，否则创建新的记录。时间根据给定的单位对齐（按小时或按分钟等）。
   - `Complete_data_start(start_time_str, data, unit)`: 根据给定的开始时间，将数据填充到指定的时间范围内，按单位增量进行填充。
   - `Complete_data_end(start_time_str, end_time_str, data, unit)`: 类似于 `Complete_data_start`，但填充至指定的结束时间。
   - `calculate_cumulative_time(fh, mh, oh, setData1, setData2, setData3)`: 根据输入的 `fh`、`mh`、`oh` 数据和预设的 `setData1`, `setData2`, `setData3` 进行时间累计的计算。

3. **路由及业务逻辑**：

   - `/flask`

     路由： 

     - 该路由接收包含多个传感器数据的 JSON 请求。
     - 数据通过 `SensorData` 类进行验证。
     - 数据校验通过后，调用 `update_data` 更新数据，并用 `Complete_data_start` 和 `Complete_data_end` 对数据进行填充。
     - 如果数据校验失败，则返回验证错误信息。
     - 返回填充后的数据列表。

   - `/flask2`

     路由： 

     - 该路由处理时间累计计算的请求，接收包含多个历史传感器数据的 JSON 请求。
     - 数据通过 `SensorData2` 类进行验证，验证通过后计算累计时间。
     - 如果数据验证失败，则返回验证错误信息。

4. **文件操作**：

   - `save_to_json(data, filename)`: 将数据保存为 JSON 格式文件。

### API 接口说明：

#### 1. `/flask`（POST）

- **请求体（JSON）**：

  ```json
  {
    "starttime": "2024-01-01 00:00:00",  // 开始时间
    "endtime": "2024-01-02 00:00:00",    // 结束时间
    "unit": 3600,                         // 时间单位（秒），例如 3600 秒代表小时
    "data": [
      {
        "tagName": "sensor1",
        "vt": 1,
        "values": [
          {"v": 25.5, "s": 1, "t": "2024-01-01 00:00:00"},
          {"v": 30.2, "s": 0, "t": "2024-01-01 01:00:00"}
        ]
      }
    ]
  }
  ```

- **返回示例（JSON）**：

  ```json
  [
    {
      "time": "2024-01-01 00:00:00",
      "sensor1": 25.5
    },
    {
      "time": "2024-01-01 01:00:00",
      "sensor1": 30.2
    }
  ]
  ```

- **功能**：

  - 校验传入的数据格式和时间递增性。
  - 更新现有数据（如果时间点已经存在）。
  - 对数据进行填充，使其包含从 `starttime` 到 `endtime` 范围内的所有时间点。

- **错误响应（如果验证失败）**：

  ```json
  {
    "status": "error",
    "message": "Validation failed for some data",
    "errors": [
      {
        "error": "ValidationError",
        "details": [
          {"loc": ["values", 0, "t"], "msg": "Invalid datetime format", "type": "value_error"}
        ]
      }
    ]
  }
  ```

#### 2. `/flask2`（POST）

- **请求体（JSON）**：

  ```json
  {
    "hist": [
      {
        "fh": [
          {"t": "2024-01-01 00:00:00", "v": 1.0},
          {"t": "2024-01-01 01:00:00", "v": 2.0}
        ],
        "mh": [
          {"t": "2024-01-01 00:00:00", "v": 1.0},
          {"t": "2024-01-01 01:00:00", "v": 2.0}
        ],
        "oh": [
          {"t": "2024-01-01 00:00:00", "v": 1.0},
          {"t": "2024-01-01 01:00:00", "v": 2.0}
        ]
      }
    ],
    "f": 1.0,
    "m": 2.0
  }
  ```

- **返回示例（JSON）**：

  ```json
  [
    "00:02:00",
    "00:02:00"
  ]
  ```

- **功能**：

  - 校验传入的数据格式。
  - 根据传入的数据计算累计时间（例如，`fh`、`mh` 和 `oh` 这些数据流的时间）。

### 异常处理：

- **时间格式校验失败**：使用 `Pydantic` 内建的验证器进行时间格式校验，如果格式不匹配，会抛出 `ValidationError`。
- **空数据校验失败**：在 `values` 列表为空时，抛出 `ValueError` 并返回错误信息。
- **时间递增性校验失败**：如果时间列表中的时间不严格递增，抛出 `ValueError` 并返回错误信息。

---------------------------------------------------------------------------------------------------------------------------------------------
### (二)project2:Trained SVR model predicts COP values
## 基本信息

- **服务地址**: `http://127.0.0.1:1820/`
- **支持的请求类型**: `POST`
- **跨域支持**: 是 (`CORS`)

------

## 接口 1: `/select_cop`

### 功能

根据输入的负荷率（`load_level`）、冷却水温度（`temperature`）和冷冻水温度（`frozen_temp`），使用已训练的 SVR 模型预测 COP 值。如果输入数据超出合理范围，则返回错误响应。

### 请求方式

```
POST
```

### 请求参数

请求体应包含以下 JSON 格式的数据：

```json
{
    "load_level": <float>,      // 负荷率（百分比，0-100）
    "temperature": <float>,     // 冷却水温度（摄氏度，0-15）
    "frozen_temp": <float>      // 冷冻水温度（摄氏度，-10到10）
}
```

### 响应

- **成功响应（200 OK）**:

  ```json
  {
      "predicted_cop": <float>   // 预测的 COP 值
  }
  ```

- **错误响应（400 Bad Request）**:

  ```json
  {
      "status": "error",
      "message": "<错误信息>"
  }
  ```

### 示例

#### 请求示例

```bash
curl -X POST http://127.0.0.1:1820/select_cop -H "Content-Type: application/json" -d '{
    "load_level": 85,
    "temperature": 12,
    "frozen_temp": 5
}'
```

#### 响应示例

```json
{
    "predicted_cop": 3.8
}
```

------

## 接口 2: `/train_cop_model`

### 功能

从指定的 URL 获取历史数据，根据这些数据训练 COP 模型，保存训练后的模型并进行可视化。

### 请求方式

```
POST
```

### 请求参数

请求体应包含以下 JSON 格式的数据：

```json
{
    "url": <string>,             // 历史数据 API 的 URL
    "data": {"load_level": "JIFANG/JIFANG/JF_COP"
	"start": "2024-07-30 00:00:00", 
    "end": "2024-07-30 20:00:00",
    "second": "60"}
}
```

### 响应

- **成功响应（200 OK）**:

  ```json
  {
      "status": "success",
      "message": "模型训练完成并保存"
  }
  ```

- **错误响应（400 Bad Request）**:

  ```json
  {
      "status": "error",
      "message": "<错误信息>"
  }
  ```

### 示例

#### 请求示例

```bash
curl -X POST http://127.0.0.1:1820/train_cop_model -H "Content-Type: application/json" -d '{
    "url": "http://example.com/data",
    "data": {
        "param1": "value1",
        "param2": "value2"
    }
}'
```

#### 响应示例

```json
{
    "status": "success",
    "message": "模型训练完成并保存"
}
```

------

## 错误处理

### 常见错误代码

- **400 Bad Request**: 请求的数据不符合预期或缺少必要的字段。
- **500 Internal Server Error**: 服务器内部错误，通常是代码或数据问题。

------

## 数据范围说明

以下是接口中涉及到的数据范围，所有输入数据必须在这些范围内，否则会返回错误响应。

- **负荷率 (load_level)**: 0% 到 100%。
- **冷却水温度 (temperature)**: 0°C 到 15°C。
- **冷冻水温度 (frozen_temp)**: -10°C 到 10°C。
- **COP (cop_data)**: 2.0 到 6.0。

------

## 定时任务说明

该应用使用 `schedule` 库执行定时任务，每小时更新缓存中的 COP 历史数据。

------

## 模型说明

使用 **SVR (支持向量回归)** 模型进行 COP 预测，模型的参数如下：

- `C = 30`
- `gamma = 0.01`

训练的数据包括：

- **负荷率**
- **冷却水温度**
- **冷冻水温度**
- **COP 值**

模型训练完成后，使用已训练的模型进行 COP 预测。

------

## 可视化

训练和优化后的 COP 模型会进行 3D 曲面图可视化，帮助展示 COP 的变化情况。

----------------------------------------------------------------------------------------------------------------------------------------

### （三）project3:List of work leave status


------

# **接口一：相似日工况报表**

## **接口名称**

```
/similar_day_calculation
```

## **接口描述**

该接口用于计算与当前日期气象与工况数据最相似的历史日期，并生成包含相关属性的计算结果。

## **请求方法**

```
POST
```

## **请求URL**

```
http://<服务器地址>/similar_day_calculation
```

## **请求头**

| 参数           | 类型   | 是否必须 | 描述                      |
| -------------- | ------ | -------- | ------------------------- |
| `Content-Type` | string | 是       | 必须为 `application/json` |

## **请求参数**

请求数据为 JSON 格式，包含以下字段：

| 参数名         | 类型   | 是否必须 | 描述                           |
| -------------- | ------ | -------- | ------------------------------ |
| `url`          | string | 是       | 获取历史数据的接口地址         |
| `data_compare` | dict   | 是       | 用于获取历史对比数据的请求参数 |
| `data`         | dict   | 是       | 用于获取当前日期数据的请求参数 |

### **请求参数示例**

```json
{
    "url": "",
    "data_compare": {
        "start": "2024-01-01 00:00:00",
        "end": "2024-01-31 23:59:59"
    },
    "data": {
        "start": "2025-01-01 00:00:00",
        "end": "2025-01-01 23:59:59"
    }
}
```

## **返回结果**

### **返回格式**

返回数据为 JSON 格式，包含与当前日期最相似的历史日期列表及相关属性计算结果。

### **返回字段说明**

| 参数名      | 类型       | 描述                                                         |
| ----------- | ---------- | ------------------------------------------------------------ |
| `variables` | list(dict) | 包含计算结果的键值对，相关属性（相似度,日期,最高气温,最低气温,白天平均温度8-18,夜晚平均温度,高峰模式运行时长,夜晚模式运行时长,空调供水温度,水源侧进水温度,冷热量,能耗）的计算值 |
|             |            |                                                              |

### **返回数据说明**

| 变量名                 | 含义             |
| ---------------------- | ---------------- |
| date                   | 日期             |
| similarity             | 相似度           |
| min_temp               | 最低气温         |
| max_temp               | 最高气温         |
| daytime_avg_temp       | 白天平均温度8-18 |
| nighttime_avg_temp     | 夜晚平均温度     |
| peak_mode_duration     | 高峰模式运行时长 |
| night_mode_duration    | 夜晚模式运行时长 |
| air_supply_temp        | 空调供水温度     |
| water_inlet_temp       | 水源侧进水温度   |
| cooling_capacity_kwh   | 冷热量KWH        |
| energy_consumption_kwh | 能耗KWH          |
| cooling_price          | 冷量单价 元/KWH  |



## **错误码**

### **返回格式**

错误时，返回 HTTP 状态码为 400，并包含错误信息。

### **错误字段说明**

| 参数名    | 类型   | 描述                     |
| --------- | ------ | ------------------------ |
| `status`  | string | 错误状态，固定为 `error` |
| `message` | string | 错误信息                 |

### **错误示例**

```json
{
    "status": "error",
    "message": "数据获取失败"
}
```

## **功能逻辑**

1. **数据获取**：
   - 调用 `fetch_history_data` 方法从指定接口获取当前日期和历史日期的气象与工况数据。
   - 数据包含：室外温度、空调供水温度、水源侧出水温度、冷热量及能耗等。
2. **数据验证**：
   - 调用 `validate_data_in_range` 方法对获取的数据进行验证，确保所有值都在预定义范围内。
   - 如果值超出范围，调整为边界值。
3. **相似日计算**：
   - 调用 `calculate_similar_dates` 方法，基于温度、日期差异及节假日差异计算相似度。
   - 返回最相似的 5 个历史日期。
4. **关联属性计算**：
   - 基于相似日期，计算相关属性（例如冷量、电耗）的统计值，生成最终结果。
5. **返回结果**：
   - 返回最相似的历史日期及计算的属性值。



# 接口二: **相似日工况曲线**

**描述:**
 获取历史数据，根据提供的相似日期，获取构建相似日的工况曲线的数据。

------

#### **请求方法:**

```
POST
```

#### **请求URL:**

```
/Operating_conditions_curve
```

------

### 请求参数说明：

#### 参数说明:

| 参数名          | 类型     | 必填 | 描述                                         |
| --------------- | -------- | ---- | -------------------------------------------- |
| `url`           | `string` | 是   | 历史数据查询的 URL，提供接口调用的地址       |
| `data_compare`  | `string` | 是   | 查询历史数据时用于对比的参数标识             |
| `data`          | `string` | 是   | 查询当天数据时的参数标识                     |
| `similar_dates` | `list`   | 是   | 用于指定相似日的日期数组，格式为`YYYY-MM-DD` |

------

#### **请求体**（JSON 格式）:

```json
{
	"url": "",
	"data_compare": {"tag": "JIFANG/JIFANG/JF_COP",
	"start": "2024-07-30 00:00:00", "end": "2024-08-30 00:00:00", "second": "600"},
	"data": {"tag": "JIFANG/JIFANG/JF_COP",
	"start": "2024-08-31 00:00:00", "end": "2024-09-1 00:00:00", "second": "600"},
	"similar_dates":[
	  "2024-08-29",
	  "2024-08-28",
	  "2024-08-27",
	  "2024-08-26",
	  "2024-08-25"
	]
}
```

### **返回数据说明**：

| 变量名           | 含义                |
| ---------------- | ------------------- |
| supply_temp      | 空调供水温度        |
| return_temp      | 空调回水温度        |
| src_in_temp      | 水源侧进水温度      |
| src_out_temp     | 水源侧出水温度      |
| out_temp         | 室外温度            |
| out_humidity     | 室外湿度            |
| out_wetbulb      | 室外湿球温度        |
| FreFB1           | 机房空调泵1频率反馈 |
| FreFB2           | 机房空调泵2频率反馈 |
| Pump_run1        | 机房空调泵1运行状态 |
| Pump_run2        | 机房空调泵2运行状态 |
| ZLJ1_COP         | 主机1COP            |
| ZLJ2_COP         | 主机2COP            |
| ZLJ1_SSLengLiang | 主机1瞬时冷量       |
| ZLJ2_SSLengLiang | 主机2瞬时冷量       |
| ZLJ1_KW          | 主机1功率           |
| ZLJ2_KW          | 主机2功率           |
| ZLJ_Now_Load1    | 主机1电流比         |
| ZLJ_Now_Load2    | 主机2电流比         |
| total_power      | 总功率              |
| cooling_capacity | 瞬时冷量            |
| total_energy     | 当前累计能耗        |
| cooling_price    | 冷量单价            |
| pump_freq        | 空调泵频率          |

**失败响应**:

```json
{
  "status": "error",
  "message": "Invalid URL or parameters"
}
```

------

# 接口三: **负荷预测** 

**描述:**
 获取历史数据，根据相似日的冷量曲线，预测今天的冷量曲线。

------

#### **请求方法:**

```
POST
```

#### **请求URL:**

```
/Load_forecasting
```

------

### 请求参数说明：

#### 参数说明:

| 参数名       | 类型     | 必填 | 描述                                           |
| ------------ | -------- | ---- | ---------------------------------------------- |
| `url`        | `string` | 是   | 历史数据查询的 URL，提供接口调用的地址         |
| similar_data | `string` | 是   | 查询相似日数据时用于对比的参数标识（一日数据） |
| `data`       | `string` | 是   | 查询当天数据时的参数标识                       |

------

#### **请求体**（JSON 格式）:

```json
{
	"url": "",
	"similar_data": {"tag": "JiFang1/SSLenLiangZ",
	"start": "2025-1-15 00:00:00", "end": "2025-1-15 23:59:59", "second": "600"},
	"data": {"tag": "JiFang1/SSLenLiangZ",
	"start": "2025-01-16 00:00:00", "end": "2025-1-16 23:59:59", "second": "600"},
}
```

### **返回数据说明**：

```json
[
  {
    "t": "2025-01-16 00:00:00", #时间
    "v": 500
  },
  {
    "t": "2025-01-16 00:10:00", #预测值
    "v": 500
  },
  ]
```



### 注意事项:

1. 确保`similar_dates`中的日期格式正确 (`YYYY-MM-DD`)。
2. `url` 必须是可以访问的历史数据查询接口。
3. 如果`similar_dates`为空，将只返回当日数据。
4. 数据验证范围已在代码中定义，如需修改，请调整对应的全局常量。
5. 数据库连接参数需在 `DB_CONFIG` 中正确配置，以确保节假日查询功能正常运行。

## **开发与调试**

- 开发语言：Python
- 框架：Flask
- 数据库：MySQL

------



# 数据库相关接口以及配置：

#### 数据库表设计：

```sql
CREATE TABLE `schedule` (
  `index` int NOT NULL AUTO_INCREMENT,
  `datetime` datetime NOT NULL,
  `holiday` int NOT NULL,
  PRIMARY KEY (`index`),
  UNIQUE KEY `datetime_UNIQUE` (`datetime`)
) ENGINE=InnoDB AUTO_INCREMENT=79 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
```

## 接口一：数据插入接口：

### 接口文件：

```python
insert_database.py       #文件执行即可
```

#### 设置时间范围：

```python
# 定义起始日期和结束日期
    start_date = date(2025, 1, 8)
    end_date = date(2025, 1, 12)
```

## 接口二：查询日期对应的工休状态：

### 接口文件：

```python
app.py 
```

**描述:**
查询一组日期对应的工休状态。

------

#### **请求方法:**

```
POST
```

#### **请求URL:**

```
/query_work_rest_status
```

------

### 请求参数说明：

------

#### **请求方式**:

```json
data = ["2025-01-14 00:00:00"]

r = post(url='http://127.0.0.1:1820/query_work_rest_status', json=data)
```

### **返回数据说明**：

```json
[
  {
    "date": "Tue, 14 Jan 2025 00:00:00 GMT",
    "status": 1  #1表示工作日，0表示休息日
  }
]
```

## 接口三：**修改一组日期对应的工休状态**：

### 接口文件：

```python
app.py 
```

**描述:**
传入参数：日期的列表，工休状态的列表，能够根据该日期列表以及其对应的公休状态列表进行修改。

------

#### **请求方法:**

```
POST
```

#### **请求URL:**

```
/update_work_rest_status
```

------

### 请求参数说明：

------

#### **请求方式**:

```json
data = {
	'dates':["2025-01-14 00:00:00"],
	'statuses':[0]
}

r = post(url='http://127.0.0.1:1820/update_work_rest_status', json=data)
```

### **返回数据说明**：

```json
{
  "status": "success",
  "updated_dates": [
    "2025-01-14 00:00:00"
  ]
}
```

