# city_risk_report.py
"""
End-to-end demo of a **two-agent workflow** that:
1. Collects live* weather data for a city (*stubbed for the demo).
2. Produces a short public-safety advisory.
3. Uses built-in tracing so every LLM call, guardrail check and tool execution
   is visible in the OpenAI Traces dashboard at https://platform.openai.com/traces
"""

import asyncio
import os
from typing import Any, Dict
from dotenv import load_dotenv

from agents import (
    Agent,
    Runner,
    trace,
    function_tool,
    RunConfig,
    GuardrailFunctionOutput,
    input_guardrail,
    InputGuardrailTripwireTriggered,
)

# ------------------------------------------------------------------
# 1. Custom tool: live weather (stubbed for demo purposes)
#    Replace with a real API such as OpenWeatherMap or Meteostat.
# ------------------------------------------------------------------
@function_tool
async def get_weather(city: str) -> Dict[str, Any]:
    """
    Fetch current weather for the requested city.

    Returns
    -------
    dict
        temperature_c : int
        humidity_pct  : int
        risk          : str  # low | medium | high
        summary       : str  # short human-readable blurb

    Raises
    ------
    ValueError
        If the city is unknown or the API quota is exceeded.
    """
    city = city.lower().strip()

    if city == "berlin":
        return {
            "temperature_c": 14,
            "humidity_pct": 83,
            "risk": "low",
            "summary": "Overcast with drizzle",
        }

    if city == "tokyo":
        return {
            "temperature_c": 32,
            "humidity_pct": 91,
            "risk": "high",
            "summary": "Heatwave advisory issued",
        }

    # --- Any city not in the stub list will raise ---
    raise ValueError(
        f"Weather data unavailable or quota exceeded for '{city}'"
    )

# ------------------------------------------------------------------
# 2. Guardrail: block unknown or unsupported cities *before* any
#    expensive LLM or tool work is done.
# ------------------------------------------------------------------
@input_guardrail
async def city_guardrail(ctx, agent, city: str) -> GuardrailFunctionOutput:
    """
    Allow only a curated whitelist of cities to keep the demo safe
    and predictable.
    """
    allowed = {"berlin", "tokyo", "london", "paris", "new york"}
    city_norm = city.lower().strip()

    if city_norm not in allowed:
        return GuardrailFunctionOutput(
            output_info=city,
            tripwire_triggered=True,
        )

    # City is allowed – proceed
    return GuardrailFunctionOutput(
        output_info=city,
        tripwire_triggered=False,
    )

# ------------------------------------------------------------------
# 3. Agent definitions
# ------------------------------------------------------------------

researcher = Agent(
    name="Researcher",
    instructions=(
        "You are a city-data researcher. "
        "Given a city name, call the `get_weather` tool and return a **compact JSON** "
        "payload with keys: temperature_c, humidity_pct, risk, summary."
    ),
    tools=[get_weather],
    input_guardrails=[city_guardrail],
)

analyst = Agent(
    name="Analyst",
    instructions=(
        "You are a public-safety analyst. "
        "Using the JSON weather summary provided by the Researcher, "
        "write a **single paragraph** advisory for residents and travellers. "
        "Be concise, actionable, and avoid technical jargon."
    ),
)

# ------------------------------------------------------------------
# 4. Orchestration + tracing
# ------------------------------------------------------------------
async def main() -> None:
    """
    Run the two-phase workflow under a single trace named "City Risk Report".

    Phase 1: Researcher → weather JSON  
    Phase 2: Analyst    → human advisory  

    All spans (guardrail, tool call, LLM calls) appear in the dashboard.
    """
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("❌  Set OPENAI_API_KEY in your environment or .env file.")
        return

    city = input("Choose a city (Berlin, Tokyo, London, Paris, New York): ").strip()
    if not city:
        print("❌  No city entered – exiting.")
        return

    # RunConfig with optional tracing metadata
    cfg = RunConfig(trace_metadata={"city": city})

    with trace("City Risk Report"):
        try:
            # ---- Phase 1: Data gathering ----
            research_result = await Runner.run(
                researcher,
                city,
                run_config=cfg,
            )

            # ---- Phase 2: Advisory generation ----
            analysis_result = await Runner.run(
                analyst,
                research_result.final_output,
                run_config=cfg,
            )

            print("\n📋  Public-Safety Advisory\n")
            print(analysis_result.final_output)

        except InputGuardrailTripwireTriggered:
            print(
                f"⚠️  Guardrail triggered: '{city}' is not on the supported list. "
                f"Please choose from Berlin, Tokyo, London, Paris, or New York."
            )

# ------------------------------------------------------------------
# 5. Entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())