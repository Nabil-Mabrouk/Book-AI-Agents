# agents/trend_judge_agent.py
from agents import Agent
from pydantic import BaseModel, Field

class TrendDecision(BaseModel):
    is_significant: bool = Field(description="True if the candlestick represents a noteworthy trend, False otherwise.")
    reasoning: str = Field(description="A brief explanation for the decision, mentioning volume or price action.")

trend_judge_agent = Agent(
    name="TrendJudgeAgent",
    instructions=(
        "You are an expert technical analyst interpreting 1-minute candlestick data. "
        "Your role is to determine if the last minute's activity is significant. "
        "Pay attention to: \n"
        "- **High Volume**: A spike in volume makes any price move more significant. \n"
        "- **Large Price Range**: A large difference between the high and low price. \n"
        "- **Strong Close**: A close price near the high (bullish) or low (bearish). \n"
        "A small candlestick on low volume is insignificant noise. Provide your decision in the required structured format."
    ),
    output_type=TrendDecision,
    model="gpt-4o-mini",
)