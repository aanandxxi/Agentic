from phi.agent import Agent
from phi.tools import Toolkit
import phi.api
from phi.model.ollama import Ollama
from phi.tools.yfinance import YFinanceTools
from phi.tools.duckduckgo import DuckDuckGo
from dotenv import load_dotenv
import os
import phi
import openmeteo_requests
import http.client, urllib.parse, json
import pandas as pd


load_dotenv()

model_id = "llama3.2"
model = Ollama(id=model_id)

web_instructions = 'Always include sources'
finance_instructions = 'Use tables to display data'
#
phi.ap = os.getenv("PHI_API_KEY")

#Forecast Tool
class GetForecast(Toolkit):
    def __init__(self):
        super().__init__()

    def get_forecast(self,location:str)->str:
        # Get coordinates for location to pull forecasts
        coord_conn = http.client.HTTPConnection('geocode.xyz')
        coord_params = urllib.parse.urlencode({
            'locate': location,
            'json': 1,
            })

        coord_conn.request('GET', '/?{}'.format(coord_params))

        res = coord_conn.getresponse()
        data = res.read()

        co_ord = json.loads(data.decode("utf-8"))
    
        # base_url variable to store url
        forecast_url = "https://api.open-meteo.com/v1/forecast"
    
        forecat_params = {
            "latitude": co_ord["latt"],
            "longitude": co_ord["longt"],
            "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_probability_max"],
            "forecast_days": 5
        }
        openmeteo = openmeteo_requests.Client()    
        forecast_res = openmeteo.weather_api(forecast_url, params=forecat_params)

        loc_response = forecast_res[0]
        daily = loc_response.Daily()
        daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()
        daily_temperature_2m_min = daily.Variables(1).ValuesAsNumpy()
        daily_precipitation_probability_max = daily.Variables(2).ValuesAsNumpy()

        daily_data = {"date": pd.date_range(
            start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
            end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = daily.Interval()),
            inclusive = "left"
        )}

        daily_data["temperature_2m_max"] = daily_temperature_2m_max
        daily_data["temperature_2m_min"] = daily_temperature_2m_min
        daily_data["precipitation_probability_max"] = daily_precipitation_probability_max

        daily_dataframe = pd.DataFrame(data = daily_data)
     
        return daily_dataframe.to_string()

#weather agent
weather_agent = Agent(
    name = "Weather Agent",
    description="You are a helpful Assistant to get world weather forecast data using tools", 
    tools=[GetForecast().get_forecast],
    model=model,
)

#Search agent
web_search_agent = Agent(
    name="Web Search Agent",
    role="Search the web for information",
    model=model,
    tools=[DuckDuckGo()],
    instruction=[web_instructions],
    show_tool_calls=True,
    markdown=True
)

#finance agent
finance_agent = Agent(
    name="Finance AI Agent",
    model=model,
    tools=[
        YFinanceTools(
            stock_price=True,
            analyst_recommendations=True,
            company_info=True,
            company_news=True,
            key_financial_ratios=True
        )
    ],
    instruction=[finance_instructions],
    show_tool_calls=True,
    markdown=True
)

# Define the Team Leader agent
agent_team = Agent(
    name="Agents Team",
    model=model,
    team=[weather_agent, finance_agent, web_search_agent],
    instructions=[
        "You are an agent that helps respond to queries related to weather forecast, web search and financial analysis",
        "You can ask Web Search Agent to search for each query to gather additional information"
        "Finance AI Agent can help pull information related to stock markets, stocks, equities etc.",
        "Provide the Weather Agent with the location to pull forecast information for that location"
        "Finally, compile a thoughtful and engaging summary."
    ],
    show_tool_calls=True,
    markdown=True,
)

agent_res = agent_team.run("What is the weather forecast in Hyderabad and share stock price for Tata Motors?")
print(agent_res.content)