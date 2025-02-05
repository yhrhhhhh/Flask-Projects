# Flask-Projects

### 说明文档：Flask API 应用

###(一)project1:Verify the incoming data format and time incrementability && Calculate accumulated time based on incoming data

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


###(二)project2:Trained SVR model predicts COP values
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

###（三）project3:List of work leave status
