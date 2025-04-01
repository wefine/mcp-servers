"""天气数据模型。

定义与天气API交互所需的数据模型。
"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class WeatherType(str, Enum):
    """天气类型枚举。"""

    LIVE = "base"  # 实况天气
    FORECAST = "all"  # 预报天气


class WeatherLiveResponse(BaseModel):
    """实况天气响应模型。"""

    province: str = Field(..., description="省份名")
    city: str = Field(..., description="城市名")
    adcode: str = Field(..., description="区域编码")
    weather: str = Field(..., description="天气现象")
    temperature: str = Field(..., description="实时温度（摄氏度）")
    wind_direction: str = Field(..., description="风向", alias="winddirection")
    wind_power: str = Field(..., description="风力级别", alias="windpower")
    humidity: str = Field(..., description="空气湿度")
    report_time: str = Field(..., description="数据发布时间", alias="reporttime")


class WeatherForecastDay(BaseModel):
    """天气预报单日数据模型。"""

    date: str = Field(..., description="预报日期")
    week: str = Field(..., description="星期几")
    day_weather: str = Field(..., description="白天天气现象", alias="dayweather")
    night_weather: str = Field(..., description="晚上天气现象", alias="nightweather")
    day_temp: str = Field(..., description="白天温度", alias="daytemp")
    night_temp: str = Field(..., description="晚上温度", alias="nighttemp")
    day_wind: str = Field(..., description="白天风向", alias="daywind")
    night_wind: str = Field(..., description="晚上风向", alias="nightwind")
    day_power: str = Field(..., description="白天风力", alias="daypower")
    night_power: str = Field(..., description="晚上风力", alias="nightpower")


class WeatherForecastResponse(BaseModel):
    """天气预报响应模型。"""

    province: str = Field(..., description="省份名")
    city: str = Field(..., description="城市名")
    adcode: str = Field(..., description="区域编码")
    report_time: str = Field(..., description="预报发布时间", alias="reporttime")
    forecasts: List[WeatherForecastDay] = Field(..., description="预报数据", alias="casts")


# API请求和响应模型
class WeatherQueryRequest(BaseModel):
    """天气查询请求模型。"""

    city: str = Field(..., description="城市编码，必须为城市的adcode")
    extensions: WeatherType = Field(WeatherType.LIVE, description="气象类型")


class WeatherResponse(BaseModel):
    """统一的天气响应模型。"""

    status: str = Field(..., description="返回状态，1表示成功")
    count: str = Field(..., description="返回结果数目")
    info: str = Field(..., description="返回的状态信息")
    infocode: str = Field(..., description="返回状态码")
    lives: Optional[List[WeatherLiveResponse]] = Field(None, description="实况天气数据")
    forecasts: Optional[List[WeatherForecastResponse]] = Field(None, description="预报天气数据")

    class Config:
        """Pydantic配置类。"""

        populate_by_name = True
