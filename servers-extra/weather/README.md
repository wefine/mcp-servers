# 天气 MCP 服务器

这是一个基于高德地图天气API的MCP服务器，使用FastMCP框架开发。该服务器提供实时天气和天气预报功能。

## 功能特点

- 获取城市实时天气数据
- 获取城市未来天气预报（通常为3天）
- 基于FastMCP框架，易于集成和扩展
- 使用.env文件管理配置，方便部署

## 安装与配置

### 前提条件

- Python 3.12 或更高版本
- UV（Python依赖管理工具）
- 高德地图开发者账号和API Key

### 安装步骤

1. 克隆本仓库

```bash
git clone <repository-url>
cd weather
```

2. 使用UV安装依赖

```bash
uv pip install -e .
```

3. 配置环境变量

复制`.env.example`文件（如果有）或创建一个新的`.env`文件，然后填入您的高德地图API密钥和其他设置：

```
# 高德地图天气API配置
AMAP_KEY=your_amap_key_here
AMAP_BASE_URL=https://restapi.amap.com/v3/weather

# 服务器配置
HOST=0.0.0.0
PORT=8000
```

## 使用方法

### 启动服务器

```bash
python main.py
```

服务器默认在 `0.0.0.0:8000` 启动，您可以通过`.env`文件修改这些设置。

### API 调用示例

服务器提供以下MCP方法：

1. **获取实时天气**

```json
{
  "name": "get_weather_live",
  "parameters": {
    "city": "110000"
  }
}
```

2. **获取天气预报**

```json
{
  "name": "get_weather_forecast",
  "parameters": {
    "city": "110000"
  }
}
```

## 城市编码参考

使用高德地图的城市编码（adcode），部分常用城市编码：

- 北京: 110000
- 上海: 310000
- 广州: 440100
- 深圳: 440300
- 杭州: 330100

更多城市编码请参考[高德地图开放平台行政区域编码](https://lbs.amap.com/api/webservice/download)

## 参考文档

- [高德地图天气API文档](https://lbs.amap.com/api/webservice/guide/api/weatherinfo/)
- [FastMCP文档](https://fastmcp.readthedocs.io/)

## 许可证

[MIT](LICENSE)
