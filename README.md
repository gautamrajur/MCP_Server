# Weather MCP Server

A Model Context Protocol (MCP) server that provides weather information, sunrise/sunset times, and manages favorite cities.

## Features

### Tools
- **get_weather** - Get current weather and temperature for any city
- **get_sunrise_and_sunset_in_EST** - Get sunrise/sunset times in EST timezone
- **add_favorite_city** - Add cities to your favorites list

### Resources
- **Weather History** - View all past weather queries
- **Favorite Cities** - Access your saved favorite cities

### Prompts
- **weather_report** - Generate detailed weather report with clothing suggestions
- **compare_cities** - Compare weather across multiple cities

## Setup

1. **Install dependencies:**
```bash
pip install mcp httpx python-dotenv
```

2. **Get API key:**
   - Sign up at [OpenWeatherMap](https://openweathermap.org/api)
   - Get a free API key

3. **Create `.env` file:**
```bash
OPENWEATHER_API_KEY=your_key_here
```

4. **Create data directory:**
```bash
mkdir -p weather_data
echo "[]" > weather_data/history.json
echo "[]" > weather_data/favorites.json
```

## Configuration

Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "weather": {
      "command": "python3",
      "args": ["/full/path/to/weather_mcp.py"]
    }
  }
}
```

## File Structure
```
.
├── weather_mcp.py          # Main MCP server
├── weather_data/
│   ├── history.json        # Weather query history
│   └── favorites.json      # Favorite cities list
└── .env                    # API key (not committed)
```

## Built With

- [MCP SDK](https://modelcontextprotocol.io) - Model Context Protocol
- [OpenWeatherMap API](https://openweathermap.org/api) - Weather data
- Python 3.x

## License

MIT