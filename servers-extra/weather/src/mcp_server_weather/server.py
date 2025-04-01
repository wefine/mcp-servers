#!/usr/bin/env python
"""天气MCP服务器

这是一个基于MCP框架的简单天气服务器，提供实时天气和天气预报功能。
"""

import os
import logging
from typing import Dict, Any
# python-dotenv包的模块名就是dotenv
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP

# 导入封装的高德天气API模块
from mcp_server_weather.gaode_weather import GaodeWeatherAPI

# 加载.env文件配置
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 创建FastMCP服务器实例
mcp = FastMCP("天气服务")

# 创建高德天气API实例
weather_api = GaodeWeatherAPI()

# 从.env文件读取服务器配置
HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", "8000"))

# 工具函数：获取实时天气
@mcp.tool()
async def get_weather_live(city: str) -> Dict[str, Any]:
    """获取实时天气数据
    
    Args:
        city: 城市的adcode编码，如北京为110000
        
    Returns:
        实时天气数据
    """
    # 调用封装的API获取实时天气
    return await weather_api.get_weather_live(city)

# 工具函数：获取天气预报
@mcp.tool()
async def get_weather_forecast(city: str) -> Dict[str, Any]:
    """获取天气预报数据，通常包含未来3天的天气预报
    
    Args:
        city: 城市的adcode编码，如北京为110000
        
    Returns:
        天气预报数据
    """
    # 调用封装的API获取天气预报
    return await weather_api.get_weather_forecast(city)

# 添加城市代码查询资源
@mcp.resource("city_codes://{province}")
def get_city_codes(province: str) -> str:
    """获取指定省份的城市代码
    
    Args:
        province: 省份名称，如北京、上海等
        
    Returns:
        该省份的主要城市及其代码
    """
    # 这里提供一些常用城市的编码
    city_codes = {
        "北京": {"北京": "110000"},
        "上海": {"上海": "310000"},
        "广东": {"广州": "440100", "深圳": "440300", "珠海": "440400"},
        "江苏": {"南京": "320100", "苏州": "320500", "无锡": "320200"},
        "浙江": {"杭州": "330100", "宁波": "330200", "温州": "330300"},
    }
    
    if province in city_codes:
        result = f"{province}省主要城市代码:\n"
        for city, code in city_codes[province].items():
            result += f"- {city}: {code}\n"
        return result
    else:
        return f"未找到 {province} 的城市代码信息。可用的省份有: " + ", ".join(city_codes.keys())
