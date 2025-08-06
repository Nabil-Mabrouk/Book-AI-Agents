# Chapitre-08/voice_pipeline_example.py

"""
End-to-end demo of a **voice-enabled AI assistant**.

This script demonstrates a full voice pipeline that:
1. Records live audio from a microphone using the `sounddevice` library.
2. Orchestrates a **Speech-to-Text → Agent Logic → Text-to-Speech** workflow.
3. The underlying agent can use tools just like a text-based agent.
4. Streams the synthesized voice response back to the user's speakers in real-time.

Prerequisites:
- A configured microphone and speakers.
- The `sounddevice` and `numpy` Python libraries (`pip install sounddevice numpy`).
"""

import asyncio
import os
import random
from dotenv import load_dotenv

import numpy as np
import sounddevice as sd

from agents import Agent, function_tool
from agents.voice import (
    AudioInput,
    SingleAgentVoiceWorkflow,
    VoicePipeline,
)


# ------------------------------------------------------------------
# 1. Audio I/O Helpers
# ------------------------------------------------------------------

def record_audio_clip(duration: int = 5, sample_rate: int = 24000) -> np.ndarray:
    """
    Records audio from the default microphone for a fixed duration.
    """
    print(f"🔴 Recording for {duration} seconds... Speak now!")
    recording = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype='int16'
    )
    sd.wait()  # Wait until recording is finished
    print("✅ Recording finished.")
    return np.squeeze(recording)


class AudioPlayer:
    """A simple class to handle streaming audio playback."""
    def __init__(self, sample_rate: int = 24000):
        self.stream = sd.OutputStream(
            samplerate=sample_rate,
            channels=1,
            dtype='int16'
        )
        self.stream.start()

    def play(self, audio_data: np.ndarray):
        """Writes an audio chunk to the output stream."""
        self.stream.write(audio_data)

    def close(self):
        """Stops and closes the audio stream to release resources."""
        self.stream.stop()
        self.stream.close()


# ------------------------------------------------------------------
# 2. Agent Definition
#    Note that the agent's logic is "modality-agnostic" - it does
#    not need to know that the input is coming from voice.
# ------------------------------------------------------------------
@function_tool
def get_weather(city: str) -> str:
    """Get the current weather for a given city."""
    # Stubbed for the demo.
    return f"The weather in {city} is {random.choice(['sunny', 'cloudy', 'rainy'])}."


voice_assistant_agent = Agent(
    name="VoiceAssistant",
    instructions="You are a friendly and helpful voice assistant. Be concise.",
    model="gpt-4o-mini",
    tools=[get_weather],
)


# ------------------------------------------------------------------
# 3. Voice Workflow and Pipeline Setup
# ------------------------------------------------------------------

# The "Workflow" defines the conversational logic. For a single-agent
# interaction, `SingleAgentVoiceWorkflow` is the standard choice.
workflow = SingleAgentVoiceWorkflow(agent=voice_assistant_agent)

# The "Pipeline" wires everything together. It handles the underlying STT
# and TTS services. By default, it uses OpenAI's models.
pipeline = VoicePipeline(workflow=workflow)


# ------------------------------------------------------------------
# 4. Main Orchestration Logic
# ------------------------------------------------------------------
async def main():
    """
    Runs the full record -> process -> playback pipeline.
    """
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("❌  Set OPENAI_API_KEY in your environment or .env file.")
        return

    # --- Step 1: Record audio from the user ---
    recorded_audio = record_audio_clip()
    audio_input = AudioInput(buffer=recorded_audio)

    # --- Step 2: Run the pipeline with the recorded audio ---
    # This call is non-blocking. It initiates the STT -> Agent -> TTS
    # process and returns a result object that can be streamed.
    result = await pipeline.run(audio_input)
    player = AudioPlayer()
    print("\n🔊 [Agent responding...]")

    # --- Step 3: Stream the resulting audio back to the player ---
    # We iterate through the event stream from the pipeline result.
    # This allows us to start playing audio as soon as the first chunk
    # is synthesized, creating a real-time feel.
    try:
        async for event in result.stream():
            if event.type == "voice_stream_event_audio" and event.data is not None:
                # This event contains a chunk of audio data from the TTS engine.
                player.play(event.data)
            elif event.type == "voice_stream_event_lifecycle" and event.event == "turn_ended":
                # This event signals that the agent has finished its turn.
                print("🏁 [Response finished]")
    finally:
        # It's important to properly close the player to release audio resources.
        # We wait a moment to ensure the last audio chunk has time to play.
        await asyncio.sleep(1)
        player.close()


# ------------------------------------------------------------------
# 5. Entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())