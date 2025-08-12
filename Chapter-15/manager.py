# manager.py
import asyncio
from agents import Runner
from rich.console import Console
from agents.voice import VoicePipeline, VoicePipelineConfig, OpenAITTS, SystemPlayer
from live_data_feed import binance_multi_kline_ticker, KlineUpdate
from agents.trend_judge_agent import trend_judge_agent, TrendDecision
from agents.market_analyst_agent import market_analyst_agent

class AnalystManager:
    def __init__(self, symbols_to_track: list[str]):
        self.console = Console()
        self.symbols = symbols_to_track
        # Use a dictionary to track the last significant price for each symbol
        self.last_significant_prices = {symbol: None for symbol in symbols_to_track}
        
        self.pipeline = VoicePipeline(
            config=VoicePipelineConfig(
                tts=OpenAITTS(model="tts-1", voice="alloy"),
                audio_out=SystemPlayer(),
            )
        )

    async def _judge_kline_trend(self, kline: KlineUpdate) -> TrendDecision:
        """Invokes the TrendJudgeAgent to classify a candlestick."""
        prompt = (
            f"Analyze the following 1-minute candlestick data for {kline.symbol}:\n"
            f"- Open: ${kline.open_price:,.2f}\n"
            f"- High: ${kline.high_price:,.2f}\n"
            f"- Low: ${kline.low_price:,.2f}\n"
            f"- Close: ${kline.close_price:,.2f}\n"
            f"- Volume: {kline.volume:,.2f}\n"
            "Is this candle significant?"
        )
        result = await Runner.run(trend_judge_agent, prompt)
        return result.final_output

    async def _get_analyst_commentary(self, kline: KlineUpdate):
        """Invokes the MarketAnalystAgent and speaks the commentary."""
        prompt = f"Provide commentary on this 1-minute candlestick for {kline.symbol}: O={kline.open_price}, H={kline.high_price}, L={kline.low_price}, C={kline.close_price}, V={kline.volume}."
        await self.pipeline.say(text_or_agent=market_analyst_agent, user_input=prompt)

    async def run(self):
        """The main event loop for the real-time analyst."""
        self.console.print(f"[bold blue]📈 Starting Real-Time Crypto Trend Analyst for: {', '.join(self.symbols)}[/bold blue]")
        self.console.print("Listening for 1-minute Kline updates. Press Ctrl+C to exit.")

        # Pass the list of symbols to our upgraded data feed function
        price_feed = binance_multi_kline_ticker(self.symbols)

        try:
            async for kline in price_feed:
                self.console.print(
                    f"1m Kline Closed for {kline.symbol}: "
                    f"O=[cyan]${kline.open_price:,.2f}[/cyan] "
                    f"H=[green]${kline.high_price:,.2f}[/green] "
                    f"L=[red]${kline.low_price:,.2f}[/red] "
                    f"C=[bold cyan]${kline.close_price:,.2f}[/bold cyan] "
                    f"V=[yellow]{kline.volume:,.2f}[/yellow]"
                )

                decision = await self._judge_kline_trend(kline)

                if isinstance(decision, TrendDecision) and decision.is_significant:
                    self.console.print(f"[bold yellow]⚖️  Judge ({kline.symbol}):[/bold yellow] Significant. Reason: {decision.reasoning}")
                    await self._get_analyst_commentary(kline)
                    # Update the last significant price for this specific symbol
                    self.last_significant_prices[kline.symbol] = kline.close_price
        except KeyboardInterrupt:
            self.console.print("\n[bold red]🛑 Analyst stopped.[/bold red]")