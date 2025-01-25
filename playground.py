from phi.agent import Agent
import phi.api
from phi.model.ollama import Ollama
from phi.tools.yfinance import YFinanceTools
from phi.tools.duckduckgo import DuckDuckGo
from dotenv import load_dotenv
import os
import phi
# from fastapi import FastAPI
from phi.playground import Playground, serve_playground_app
#
load_dotenv()
web_instructions = 'Always include sources'
finance_instructions = 'Use tables to display data'

model_id = "llama3.2"
model = Ollama(id=model_id)
#
phi.ap = os.getenv("PHI_API_KEY")

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

app = Playground(agents=[finance_agent, web_search_agent]).get_app()

if __name__ == "__main__":
    serve_playground_app("playground:app", reload=True)

# agent_team = Agent(
#     model=model,
#     team=[web_search_agent, finance_agent],
#     instructions=[web_instructions, finance_instructions],
#     show_tool_calls=True,
#     markdown=True,
# )

# agent_team.print_response("Share latest news for Tesla and pull latest analyst recommendations from Yahoo Finance", stream=True)