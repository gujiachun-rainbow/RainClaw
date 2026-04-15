import logging
from typing import Dict, Any

import httpx
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

AMAP_KEY = "58b7a627c8d40bbac5062c9e9611c3ae"


@tool
def query_weather(city: str, extensions: str = "all") -> Dict[str, Any]:
    """查询指定城市的实时天气和未来天气预报。

    使用高德地图天气查询 API，支持中文城市名。
    返回实时天气（温度、湿度、风力、天气状况）和未来3天预报。

    当用户询问天气、气温、降雨、湿度、风力、穿衣建议、出行建议等天气相关话题时使用。

    Args:
        city: 城市名称（如"北京"、"上海"、"苏州"）
        extensions: 返回内容类型，"base" 为实况天气，"all" 为实况+预报，默认 "all"

    Returns:
        包含天气信息的字典，包括：
        - city_info: 城市基本信息（名称、adcode）
        - current: 实时天气（温度、湿度、风向、风力、天气描述、数据发布时间）
        - forecast: 未来天气列表（日期、白天/夜间天气、最高/最低温度、风向风力）
        - error: 错误信息（仅当查询失败时）
    """
    logger.info(f"[query_weather] params: city={city}, extensions={extensions}")

    try:
        # 1. 城市名 → adcode（行政区查询API）
        district_resp = httpx.get(
            "https://restapi.amap.com/v3/config/district",
            params={
                "keywords": city,
                "subdistrict": 0,
                "key": AMAP_KEY,
            },
            timeout=10,
        )
        district_resp.raise_for_status()
        district_data = district_resp.json()

        districts = district_data.get("districts", [])
        if not districts:
            logger.warning(f"[query_weather] city not found: {city}")
            return {"error": f"未找到城市: {city}"}

        adcode = districts[0].get("adcode", "")
        city_name = districts[0].get("name", city)
        logger.info(f"[query_weather] resolved: {city_name} -> adcode={adcode}")

        # 2. 查询天气
        weather_resp = httpx.get(
            "https://restapi.amap.com/v3/weather/weatherInfo",
            params={
                "city": adcode,
                "key": AMAP_KEY,
                "extensions": extensions,
            },
            timeout=10,
        )
        weather_resp.raise_for_status()
        weather_data = weather_resp.json()

        # 检查高德API返回状态
        if weather_data.get("status") != "1":
            info = weather_data.get("info", "未知错误")
            infocode = weather_data.get("infocode", "")
            logger.error(f"[query_weather] amap error: {info} (code={infocode})")
            return {"error": f"高德API返回错误: {info} (code={infocode})"}

        result: Dict[str, Any] = {
            "city_info": {
                "name": city_name,
                "adcode": adcode,
            }
        }

        if extensions == "base":
            # 实况天气
            lives = weather_data.get("lives", [])
            if lives:
                live = lives[0]
                result["current"] = {
                    "province": live.get("province", ""),
                    "city": live.get("city", ""),
                    "weather": live.get("weather", ""),
                    "temperature": live.get("temperature", ""),
                    "winddirection": live.get("winddirection", ""),
                    "windpower": live.get("windpower", ""),
                    "humidity": live.get("humidity", ""),
                    "reporttime": live.get("reporttime", ""),
                }
        else:
            # 实况 + 预报
            forecasts = weather_data.get("forecasts", [])
            if forecasts:
                fc = forecasts[0]
                result["city_info"]["province"] = fc.get("province", "")
                result["forecast"] = []

                casts = fc.get("casts", [])
                for i, cast in enumerate(casts):
                    day_info = {
                        "date": cast.get("date", ""),
                        "week": cast.get("week", ""),
                        "dayweather": cast.get("dayweather", ""),
                        "nightweather": cast.get("nightweather", ""),
                        "daytemp": cast.get("daytemp", ""),
                        "nighttemp": cast.get("nighttemp", ""),
                        "daywind": cast.get("daywind", ""),
                        "nightwind": cast.get("nightwind", ""),
                        "daypower": cast.get("daypower", ""),
                        "nightpower": cast.get("nightpower", ""),
                    }
                    result["forecast"].append(day_info)

                    # 第一个 cast 的实时数据作为 current
                    if i == 0:
                        result["current"] = {
                            "weather": cast.get("dayweather", ""),
                            "temperature": cast.get("daytemp", ""),
                            "winddirection": cast.get("daywind", ""),
                            "windpower": cast.get("daypower", ""),
                            "humidity": "",
                            "reporttime": fc.get("reporttime", ""),
                        }

        logger.info(f"[query_weather] success: {city_name}")
        return result

    except httpx.HTTPStatusError as exc:
        logger.error(f"[query_weather] HTTP error: {exc}")
        return {"error": f"HTTP请求失败: {exc}"}
    except Exception as exc:
        logger.error(f"[query_weather] failed: {exc}")
        return {"error": str(exc)}
