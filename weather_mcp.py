import asyncio
import json
from pathlib import Path
from mcp.server import Server
from mcp.types import Tool, TextContent, Resource, Prompt, PromptMessage, GetPromptResult
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

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "weather_data"
HISTORY_FILE = DATA_DIR / "history.json"
FAVOURITES_FILE = DATA_DIR / "favorites.json"

app = Server("weather-server")

#Tools
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
        ),
         Tool(
            name = "add_favorite_city",
            description = "Add a favorite city to list",
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
    
    #Handle add_favorite_city
    if name == "add_favorite_city":
        with open(FAVOURITES_FILE, 'r') as f:
            favorites = json.loads(f.read())
        
        if city not in favorites:
            favorites.append(city)
            with open(FAVOURITES_FILE, 'w') as f:
                f.write(json.dumps(favorites, indent=2))
            return [TextContent(type="text", text=f"Added {city} to favorites")]
        else:
            return [TextContent(type="text", text=f"{city} already in favorites")]
    
    # Only called for a weather tool
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={'q': city, "appid": API_KEY, "units": "metric"}
        )
        response.raise_for_status() 
        data = response.json()

        with open(HISTORY_FILE, 'r') as f:
            history = json.loads(f.read())
            
        history.append({
            "city": city,
            "temp": data['main']['temp'],
            "description": data['weather'][0]['description'],
            "timestamp": datetime.now().isoformat()
        })
        with open(HISTORY_FILE, 'w') as f:
            f.write(json.dumps(history, indent = 2))

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

 #Resources
@app.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="weather://history", #Virttual address, resolves on read_resource()
            name="Weather History",
            mimeType="application/json",
            description="All past weather queries"
        ),
        Resource(
            uri="weather://favorites",
            name="Favorite Cities",
            mimeType="application/json",
            description="List of favourite cities"
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    if uri == "weather://history":
        with open(HISTORY_FILE, 'r') as f:
            return f.read()
    elif uri == "weather://favorites":
        with open(FAVOURITES_FILE, 'r') as f:
            return f.read()
    else:
        raise ValueError(f"Unknow resource: {uri}")


#Prompts
@app.list_prompts()
async def list_prompts() -> list[Prompt]:
    return [
        Prompt(
            name = "weather_report",
            description = "Detailed weather report with clothing suggestions",
            arguments = [{
                "name" : "city",
                "description": "City Name",
                "required": True
            }]
        ),
        Prompt(
            name = "compare_cities",
            description = "Compare weather between cities",
            arguments = [{
                "name" : "cities",
                "description": "Comma-sepearted cities",
                "required": True
            }]
        )
    ]

@app.get_prompt()
async def get_prompt(name: str, arguments: dict) -> GetPromptResult:
    if name == "weather_report":
        city = arguments['city']
        return GetPromptResult(
            messages = [
                PromptMessage(
                    role = "user",
                    content = TextContent(
                        type = "text",
                        text = f"Get weather for {city}. Tell me the temp, conditions, what to wear, and activity suggestions. "
                    )
                )
            ]
        )
    elif name == "compare_cities":
        cities = arguments['cities']
        return GetPromptResult(
            messages = [
                PromptMessage(
                    role= "user",
                    content= TextContent(
                        type = "text",
                        text=f"Get weather for {cities} and compare temps and conditions. Which is best for outdoor activities?"
                    )
                )
            ]
        )

async def main():
    async with mcp.server.stdio.stdio_server() as (read,write):
        await app.run(read, write, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())