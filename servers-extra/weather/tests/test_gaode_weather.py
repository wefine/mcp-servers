#!/usr/bin/env python
"""高德天气API封装模块的测试

此模块包含对高德天气API封装的单元测试，使用pytest框架和mock来进行测试。
"""

import os
import json
import pytest
from unittest import mock
import httpx
from httpx import Response

from mcp_server_weather.gaode_weather import GaodeWeatherAPI


@pytest.fixture
def weather_api():
    """创建一个测试用的天气API实例"""
    return GaodeWeatherAPI(api_key="test_key", base_url="https://test.example.com/v3/weather")


@pytest.fixture
def mock_httpx_client():
    """模拟httpx客户端的响应"""
    with mock.patch("httpx.AsyncClient") as mock_client:
        client_instance = mock.AsyncMock()
        mock_client.return_value.__aenter__.return_value = client_instance
        yield client_instance


class TestGaodeWeatherAPI:
    """测试高德天气API封装类"""

    @pytest.mark.asyncio
    async def test_get_weather_live_success(self, weather_api, mock_httpx_client):
        """测试成功获取实时天气数据"""
        # 准备模拟的响应数据
        mock_response = {
            "status": "1",
            "count": "1",
            "info": "OK",
            "lives": [
                {
                    "province": "北京",
                    "city": "北京市",
                    "adcode": "110000",
                    "weather": "晴",
                    "temperature": "25",
                    "winddirection": "西",
                    "windpower": "4",
                    "humidity": "30",
                    "reporttime": "2025-04-01 15:00:00"
                }
            ]
        }
        
        # 设置模拟响应
        mock_response_obj = Response(
            status_code=200,
            content=json.dumps(mock_response).encode(),
            request=httpx.Request("GET", "https://test.example.com/v3/weather/weatherInfo")
        )
        mock_httpx_client.get.return_value = mock_response_obj
        
        # 调用测试目标
        result = await weather_api.get_weather_live("110000")
        
        # 验证结果
        assert result["province"] == "北京"
        assert result["city"] == "北京市"
        assert result["weather"] == "晴"
        assert result["temperature"] == "25"
        
        # 验证API调用
        mock_httpx_client.get.assert_called_once()
        args, kwargs = mock_httpx_client.get.call_args
        assert args[0] == "https://test.example.com/v3/weather/weatherInfo"
        assert kwargs["params"]["city"] == "110000"
        assert kwargs["params"]["key"] == "test_key"
        assert kwargs["params"]["extensions"] == "base"

    @pytest.mark.asyncio
    async def test_get_weather_live_error_response(self, weather_api, mock_httpx_client):
        """测试API返回错误响应的情况"""
        # 准备模拟的错误响应数据
        mock_response = {
            "status": "0",
            "info": "INVALID_KEY",
            "infocode": "10001"
        }
        
        # 设置模拟响应
        mock_response_obj = Response(
            status_code=200,
            content=json.dumps(mock_response).encode(),
            request=httpx.Request("GET", "https://test.example.com/v3/weather/weatherInfo")
        )
        mock_httpx_client.get.return_value = mock_response_obj
        
        # 调用测试目标
        result = await weather_api.get_weather_live("110000")
        
        # 验证结果
        assert "error" in result
        assert "API返回的数据格式不正确" in result["error"]
        assert result["raw_response"]["status"] == "0"
        assert result["raw_response"]["info"] == "INVALID_KEY"

    @pytest.mark.asyncio
    async def test_get_weather_live_http_error(self, weather_api, mock_httpx_client):
        """测试HTTP请求失败的情况"""
        # 设置模拟HTTP错误
        mock_httpx_client.get.side_effect = httpx.HTTPError("网络连接错误")
        
        # 调用测试目标
        result = await weather_api.get_weather_live("110000")
        
        # 验证结果
        assert "error" in result
        assert "获取天气数据失败" in result["error"]

    @pytest.mark.asyncio
    async def test_get_weather_forecast_success(self, weather_api, mock_httpx_client):
        """测试成功获取天气预报数据"""
        # 准备模拟的响应数据
        mock_response = {
            "status": "1",
            "count": "1",
            "info": "OK",
            "forecasts": [
                {
                    "city": "北京市",
                    "adcode": "110000",
                    "province": "北京",
                    "reporttime": "2025-04-01 15:00:00",
                    "casts": [
                        {
                            "date": "2025-04-01",
                            "week": "2",
                            "dayweather": "晴",
                            "nightweather": "多云",
                            "daytemp": "28",
                            "nighttemp": "15",
                            "daywind": "西",
                            "nightwind": "西",
                            "daypower": "4",
                            "nightpower": "3"
                        },
                        {
                            "date": "2025-04-02",
                            "week": "3",
                            "dayweather": "多云",
                            "nightweather": "小雨",
                            "daytemp": "25",
                            "nighttemp": "14",
                            "daywind": "南",
                            "nightwind": "南",
                            "daypower": "3",
                            "nightpower": "3"
                        }
                    ]
                }
            ]
        }
        
        # 设置模拟响应
        mock_response_obj = Response(
            status_code=200,
            content=json.dumps(mock_response).encode(),
            request=httpx.Request("GET", "https://test.example.com/v3/weather/weatherInfo")
        )
        mock_httpx_client.get.return_value = mock_response_obj
        
        # 调用测试目标
        result = await weather_api.get_weather_forecast("110000")
        
        # 验证结果
        assert result["city"] == "北京市"
        assert result["province"] == "北京"
        assert len(result["casts"]) == 2
        assert result["casts"][0]["date"] == "2025-04-01"
        assert result["casts"][0]["dayweather"] == "晴"
        assert result["casts"][1]["date"] == "2025-04-02"
        assert result["casts"][1]["dayweather"] == "多云"
        
        # 验证API调用
        mock_httpx_client.get.assert_called_once()
        args, kwargs = mock_httpx_client.get.call_args
        assert args[0] == "https://test.example.com/v3/weather/weatherInfo"
        assert kwargs["params"]["city"] == "110000"
        assert kwargs["params"]["extensions"] == "all"


# 如果直接运行此文件，则执行测试
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
