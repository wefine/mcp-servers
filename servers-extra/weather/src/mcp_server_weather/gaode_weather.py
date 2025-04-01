#!/usr/bin/env python
"""高德天气API封装

封装高德地图API的天气查询功能，提供实时天气和天气预报功能。
"""

import os
import logging
import httpx
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 加载.env文件配置
load_dotenv()

# 从.env文件读取高德地图API配置
AMAP_KEY = os.environ.get("AMAP_KEY", "your_amap_key_here")
AMAP_BASE_URL = os.environ.get("AMAP_BASE_URL", "https://restapi.amap.com/v3/weather")


class GaodeWeatherAPI:
    """高德天气API封装类"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """初始化高德天气API封装

        Args:
            api_key: 高德API密钥，默认从环境变量获取
            base_url: 高德天气API基础URL，默认从环境变量获取
        """
        self.api_key = api_key or AMAP_KEY
        self.base_url = base_url or AMAP_BASE_URL
        
        if self.api_key == "your_amap_key_here":
            logger.warning("使用了默认的API密钥，请在.env文件中设置正确的AMAP_KEY")

    async def get_weather_live(self, city: str) -> Dict[str, Any]:
        """获取实时天气数据
        
        Args:
            city: 城市的adcode编码，如北京为110000
            
        Returns:
            实时天气数据
        """
        logger.info(f"获取城市 {city} 的实时天气")
        
        try:
            # 构建请求参数
            params = {
                "key": self.api_key,
                "city": city,
                "extensions": "base",  # 实时天气
                "output": "JSON",
            }

            # 发送请求
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/weatherInfo", params=params)
                response.raise_for_status()
                data = response.json()

            # 检查API响应状态
            if data.get("status") == "1" and data.get("lives") and len(data["lives"]) > 0:
                return data["lives"][0]
            else:
                return {"error": "API返回的数据格式不正确", "raw_response": data}
        
        except Exception as e:
            logger.error(f"获取天气数据时出错: {e}")
            return {"error": f"获取天气数据失败: {str(e)}"}

    async def get_weather_forecast(self, city: str) -> Dict[str, Any]:
        """获取天气预报数据，通常包含未来3天的天气预报
        
        Args:
            city: 城市的adcode编码，如北京为110000
            
        Returns:
            天气预报数据
        """
        logger.info(f"获取城市 {city} 的天气预报")
        
        try:
            # 构建请求参数
            params = {
                "key": self.api_key,
                "city": city,
                "extensions": "all",  # 天气预报
                "output": "JSON",
            }

            # 发送请求
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/weatherInfo", params=params)
                response.raise_for_status()
                data = response.json()

            # 检查API响应状态
            if data.get("status") == "1" and data.get("forecasts") and len(data["forecasts"]) > 0:
                return data["forecasts"][0]
            else:
                return {"error": "API返回的数据格式不正确", "raw_response": data}
        
        except Exception as e:
            logger.error(f"获取天气预报数据时出错: {e}")
            return {"error": f"获取天气预报数据失败: {str(e)}"}


# 创建默认的API实例，方便直接导入使用
default_api = GaodeWeatherAPI()

# 为了便于使用，提供与之前相同的函数接口
async def get_weather_live(city: str) -> Dict[str, Any]:
    """获取实时天气数据（使用默认API实例）
    
    Args:
        city: 城市的adcode编码，如北京为110000
        
    Returns:
        实时天气数据
    """
    return await default_api.get_weather_live(city)


async def get_weather_forecast(city: str) -> Dict[str, Any]:
    """获取天气预报数据（使用默认API实例）
    
    Args:
        city: 城市的adcode编码，如北京为110000
        
    Returns:
        天气预报数据
    """
    return await default_api.get_weather_forecast(city)
