from phi.agent import Agent
from phi.tools import Toolkit
import phi.api
from phi.model.ollama import Ollama
from dotenv import load_dotenv
import os
import phi
# 
import openmeteo_requests
import http.client, urllib.parse, json
import pandas as pd
# 
# from fastapi import FastAPI
# from phi.playground import Playground, serve_playground_app
#
load_dotenv()

model_id = "llama3.2"
model = Ollama(id=model_id)
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


weather_agent = Agent(
    description="You are a helpful Assistant to get world weather forecast data using tools", 
    tools=[GetForecast().get_forecast],
    model=model,
)

agent_res = weather_agent.run("What's rain forecast in London?")
print(agent_res.content)

# app = Playground(agents=[finance_agent, web_search_agent]).get_app()

# if __name__ == "__main__":
#     serve_playground_app("playground:app", reload=True)

# agent_team = Agent(
#     model=model,
#     team=[web_search_agent, finance_agent],
#     instructions=[web_instructions, finance_instructions],
#     show_tool_calls=True,
#     markdown=True,
# )

# agent_team.print_response("Summarize analyst recommendations and share the latest news for NVDA", stream=True)