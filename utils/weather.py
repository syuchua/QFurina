# weather.py

from app.logger import logger
import aiohttp
from utils.city_codes import get_city_code, get_city_name


WEATHER_BASE_URL = 'https://restapi.amap.com/v3/weather/weatherInfo'
AMAP_API_KEY = 'your_api_key'


async def get_weather(city):
    city_code = get_city_code(city)
    if not city_code:
        logger.warning(f"City code not found for: {city}")
        return f"抱歉，未找到 {city} 的城市编码。请检查城市名称是否正确。"

    params = {
        "key": AMAP_API_KEY,
        "city": city_code,
        "extensions": "base",
        "output": "JSON"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(WEATHER_BASE_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["status"] == "1":  # API 调用成功
                        weather = data["lives"][0]
                        return f"{city}天气：{weather['weather']}，温度：{weather['temperature']}°C，湿度：{weather['humidity']}%，风向：{weather['winddirection']}，风力：{weather['windpower']}级"
                    else:
                        logger.error(f"Weather API error: {data['info']}")
                        return f"获取{city}天气信息失败：{data['info']}"
                else:
                    logger.error(f"Weather API request failed with status code: {response.status}")
                    return f"天气信息获取失败（状态码：{response.status}），请稍后再试"
    except Exception as e:
        logger.error(f"Error in get_weather: {e}")
        return f"获取天气信息时发生错误：{str(e)}"

async def get_forecast(city):
    city_code = get_city_code(city)
    if not city_code:
        logger.warning(f"City code not found for: {city}")
        return f"抱歉，未找到 {city} 的城市编码。请检查城市名称是否正确。"

    params = {
        "key": AMAP_API_KEY,
        "city": city_code,
        "extensions": "all",
        "output": "JSON"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(WEATHER_BASE_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["status"] == "1":  # API 调用成功
                        forecasts = data["forecasts"][0]["casts"]
                        result = f"{city}未来3天天气预报：\n"
                        for forecast in forecasts[:3]:  # 只取未来3天的预报
                            result += f"{forecast['date']}：白天{forecast['dayweather']}，夜间{forecast['nightweather']}，温度：{forecast['nighttemp']}°C - {forecast['daytemp']}°C\n"
                        return result.strip()
                    else:
                        logger.error(f"Weather forecast API error: {data['info']}")
                        return f"获取{city}天气预报失败：{data['info']}"
                else:
                    logger.error(f"Weather forecast API request failed with status code: {response.status}")
                    return f"天气预报获取失败（状态码：{response.status}），请稍后再试"
    except Exception as e:
        logger.error(f"Error in get_forecast: {e}")
        return f"获取天气预报时发生错误：{str(e)}"