import asyncio
import json
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio
import httpx
import os
from dotenv import load_dotenv
load_dotenv()

from datetime import datetime
from zoneinfo import ZoneInfo

API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not API_KEY:
    raise ValueError("OPENWEATHER_API_KEY value is not set.")

app = Server("weather-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name = "get_weather",
            description = "Get the current weather for a city. Returns temperature and conditions.",
            inputSchema = {
                "type": "object",
                "properties" : {
                    "city": {
                        "type": "string",
                        "description": "City name (e.g. 'London', 'NewYork')"
                    }
                },
                "required": ["city"]
            }
        ),
        Tool(
            name = "get_sunrise_and_sunset_in_EST",
            description = "Get the sunrise and sunset for a city. Returns sunrise and sunset timings.",
            inputSchema = {
                "type": "object",
                "properties" : {
                    "city": {
                        "type": "string",
                        "description": "City name (e.g. 'London', 'NewYork')"
                    }
                },
                "required": ["city"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    city = arguments["city"]
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={'q': city, "appid": API_KEY, "units": "metric"}
        )
        response.raise_for_status() 
        data = response.json()
    
    if name == "get_weather":
        result = f"{city}: {data['main']['temp']}°C, {data['weather'][0]['description']}"
    
    elif name == "get_sunrise_and_sunset_in_EST":
        time_zone = ZoneInfo('America/New_York')

        sunrise_est = datetime.fromtimestamp(data['sys']['sunrise'], time_zone)
        sunset_est = datetime.fromtimestamp(data['sys']['sunset'], time_zone)
        
        result = (f"In {city}, the sun rises at {sunrise_est.strftime('%I:%M %p')} EST "
                  f"and sets at {sunset_est.strftime('%I:%M %p')} EST")
    
    else:
        raise ValueError(f"Unknown tool: {name}")

    return [TextContent(type="text", text=result)]

        

async def main():
    async with mcp.server.stdio.stdio_server() as (read,write):
        await app.run(read, write, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())