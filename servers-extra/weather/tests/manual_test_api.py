#!/usr/bin/env python
"""
手动测试高德天气API封装

这个脚本直接调用GaodeWeatherAPI类的方法进行测试，不使用pytest框架。
可以用于开发过程中的快速测试和调试。
"""

import asyncio
import os
import sys
import logging
from typing import Dict, Any
from pathlib import Path

# 添加项目根目录到Python路径，以便导入项目模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.mcp_server_weather.gaode_weather import GaodeWeatherAPI

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()


async def test_live_weather(api: GaodeWeatherAPI, city_code: str) -> None:
    """测试获取实时天气"""
    logger.info(f"测试获取城市 {city_code} 的实时天气")
    result = await api.get_weather_live(city_code)
    
    if "error" in result:
        logger.error(f"获取实时天气失败: {result['error']}")
    else:
        logger.info(f"城市: {result.get('city')}")
        logger.info(f"天气: {result.get('weather')}")
        logger.info(f"温度: {result.get('temperature')}°C")
        logger.info(f"湿度: {result.get('humidity')}%")
        logger.info(f"风向: {result.get('winddirection')}")
        logger.info(f"风力: {result.get('windpower')}")
        logger.info(f"报告时间: {result.get('reporttime')}")


async def test_forecast_weather(api: GaodeWeatherAPI, city_code: str) -> None:
    """测试获取天气预报"""
    logger.info(f"测试获取城市 {city_code} 的天气预报")
    result = await api.get_weather_forecast(city_code)
    
    if "error" in result:
        logger.error(f"获取天气预报失败: {result['error']}")
    else:
        logger.info(f"城市: {result.get('city')}")
        logger.info(f"报告时间: {result.get('reporttime')}")
        
        casts = result.get('casts', [])
        for i, forecast in enumerate(casts):
            logger.info(f"\n日期 {i+1}: {forecast.get('date')}")
            logger.info(f"  白天天气: {forecast.get('dayweather')}, 温度: {forecast.get('daytemp')}°C")
            logger.info(f"  夜间天气: {forecast.get('nightweather')}, 温度: {forecast.get('nighttemp')}°C")


async def main():
    """主函数"""
    # 使用默认配置创建API实例
    api = GaodeWeatherAPI()
    
    # 测试北京和深圳的天气
    city_codes = ["110000", "440300"]  # 北京, 深圳
    
    for city_code in city_codes:
        logger.info("=" * 50)
        await test_live_weather(api, city_code)
        logger.info("-" * 30)
        await test_forecast_weather(api, city_code)
        logger.info("=" * 50)
        logger.info("\n")


if __name__ == "__main__":
    asyncio.run(main())
