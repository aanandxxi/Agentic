from phi.agent import Agent
from phi.tools import Toolkit
import phi.api
from phi.model.groq import Groq
from phi.tools.yfinance import YFinanceTools
from phi.tools.duckduckgo import DuckDuckGo
from phi.storage.agent.sqlite import SqlAgentStorage
from phi.playground import Playground, serve_playground_app
from dotenv import load_dotenv
import os
import phi
import openmeteo_requests
import http.client, urllib.parse, json
import pandas as pd
from phi.agent import Agent

load_dotenv()

phi.ap = os.getenv("PHI_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

model_id = "llama-3.3-70b-versatile"
model = Groq(id=model_id, api_key=groq_api_key)

web_instructions = "Always include sources you used to generate the answer."
finance_instructions = 'Use tables to display data where possible.'
#
# Create a storage backend using the Sqlite database
storage = SqlAgentStorage(
    # store sessions in the ai.sessions table
    table_name="agent_sessions",
    # db_file: Sqlite database file
    db_file="tmp/agent_sessions.db",
)

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
    

# Define the Team Leader agent
agent_team = Agent(
    name="Agents Team",
    model=model,
    tools = [GetForecast().get_forecast, DuckDuckGo(), YFinanceTools(stock_price=True,
            analyst_recommendations=True,
            company_info=True,
            company_news=True,
            key_financial_ratios=True)],
    add_history_to_messages=True,
    num_history_responses=3,
    markdown=True,
    # storage = storage,
    instructions=["You are a helpful agent that responds in a polite and positive manner.",
        "session_handler is capable of providing a list of existing user sessions.",
        "If user asks to continue the conversation from a previous session, display the list of sessions received from session_handler.",
        "If user provides an ID of the existing session then ask session handler to continue conversation for the selected session.",
        "You can search the web to gather additional information",
        "You can pull financial data and perform financial analysis",
        "You can pull weather forecast information for a location",
        "Always include sources you used to generate the answer.",
        "Use tables to display data where possible.",
        "Finally, compile a thoughtful summary."]
)

#List all stored sessions
agtSsn = storage.get_all_sessions()
for session in agtSsn:
    print(session.session_id, session.memory["runs"][0]["message"]["content"])

agent_team.print_response("I would like to continue a previous conversation.", stream=True)


# app = Playground(agents=[agent_team]).get_app()

# if __name__ == "__main__":
#     serve_playground_app("multi_agent:app", reload=True)

