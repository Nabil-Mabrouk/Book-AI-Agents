#
# Chapter-09/demo.py
#
# This script provides a demonstration of a real-time voice agent.
# It captures audio from the microphone, sends it to an OpenAI agent, receives
# audio back, and plays it through the speakers.
#

import asyncio
import queue
import sys
import threading
from typing import Any

import numpy as np
import sounddevice as sd

# Import the necessary components from the openai-agents library.
from agents import function_tool
from agents.realtime import (
    RealtimeAgent,
    RealtimeRunner,
    RealtimeSession,
    RealtimeSessionEvent,
)

# --- Audio Configuration ---
# These constants define the properties of the audio streams (both input and output).
# They need to be consistent for recording and playback to work correctly.

# CHUNK_LENGTH_S: The duration of each audio chunk in seconds.
# A smaller value reduces latency but may increase overhead. 50ms is a common choice.
CHUNK_LENGTH_S = 0.05

# SAMPLE_RATE: The number of audio samples captured per second.
# 24000 Hz is a good balance between quality and bandwidth for voice applications.
SAMPLE_RATE = 24000

# FORMAT: The data type for each audio sample.
# np.int16 is a 16-bit integer format, standard for PCM audio.
FORMAT = np.int16

# CHANNELS: The number of audio channels. 1 for mono, 2 for stereo.
# Voice applications typically use mono.
CHANNELS = 1


# --- Agent Definition ---
# Here, we define the AI agent's behavior, tools, and identity.

@function_tool
def get_weather(city: str) -> str:
    """
    A simple tool that the agent can choose to call.
    The @function_tool decorator makes this Python function available to the agent.
    The agent will use the function's docstring to understand what it does.
    """
    return f"The weather in {city} is sunny."


# Instantiate the RealtimeAgent.
agent = RealtimeAgent(
    name="Assistant",
    # The instructions give the agent its persona and core directives.
    instructions="You always greet the user with 'Top of the morning to you'.",
    # The 'tools' list makes the decorated functions available for the agent to use.
    tools=[get_weather],
)

# --- Helper Function ---
def _truncate_str(s: str, max_length: int) -> str:
    """A small utility to shorten long strings for cleaner console logging."""
    if len(s) > max_length:
        return s[:max_length] + "..."
    return s


# --- Main Demo Class ---
class NoUIDemo:
    """
    This class encapsulates all the logic for running the command-line demo,
    including session management, audio input/output, and event handling.
    """

    def __init__(self) -> None:
        """Initializes the state for the demo session."""
        # The agent's session, which will be created when we connect.
        self.session: RealtimeSession | None = None
        # The input audio stream from the microphone.
        self.audio_stream: sd.InputStream | None = None
        # The output audio stream for playing the agent's responses.
        self.audio_player: sd.OutputStream | None = None
        # A flag to control the recording loop.
        self.recording = False

        # --- Audio Output State Management ---
        # This section handles the complexities of playing a continuous stream of audio
        # chunks as they arrive from the server.

        # A thread-safe queue to hold incoming audio chunks from the agent.
        # The audio output callback will pull from this queue. A maxsize helps prevent
        # runaway memory usage if the consumer (audio callback) can't keep up.
        self.output_queue: queue.Queue[Any] = queue.Queue(maxsize=30)

        # An event flag used to signal an interruption (e.g., user starts speaking
        # again). This tells the output callback to immediately stop playing and
        # clear its buffered audio.
        self.interrupt_event = threading.Event()

        # The current audio chunk being played by the callback.
        self.current_audio_chunk: np.ndarray | None = None
        # The index of the next sample to be played from the current_audio_chunk.
        self.chunk_position = 0

    def _output_callback(self, outdata: np.ndarray, frames: int, time, status) -> None:
        """
        This is the heart of the audio playback system. It's called by the sounddevice
        library in a separate thread whenever it needs more audio data to play.
        It must fill the `outdata` buffer with `frames` number of samples.
        This design is crucial for low-latency, uninterrupted audio playback.
        """
        if status:
            # Log any potential issues reported by the audio device.
            print(f"Output callback status: {status}")

        # Check if an interruption has been signaled.
        if self.interrupt_event.is_set():
            # If so, clear the entire buffer of pending audio.
            while not self.output_queue.empty():
                try:
                    self.output_queue.get_nowait()
                except queue.Empty:
                    break
            # Discard any partially played chunk.
            self.current_audio_chunk = None
            self.chunk_position = 0
            # Reset the interrupt flag.
            self.interrupt_event.clear()
            # Fill the output buffer with silence.
            outdata.fill(0)
            return

        # --- Fill the Output Buffer (`outdata`) ---
        # This loop populates the `outdata` buffer with audio from our queue.
        samples_filled = 0
        while samples_filled < frames:
            # If we've finished playing the current chunk, get a new one from the queue.
            if self.current_audio_chunk is None:
                try:
                    self.current_audio_chunk = self.output_queue.get_nowait()
                    self.chunk_position = 0
                except queue.Empty:
                    # The queue is empty. This means we have no audio to play right now.
                    # This can cause a brief moment of silence (an "underrun").
                    # We break the loop and the rest of `outdata` will remain silent.
                    break

            # Determine how many samples we can copy in this iteration.
            remaining_output = frames - samples_filled
            remaining_chunk = len(self.current_audio_chunk) - self.chunk_position
            samples_to_copy = min(remaining_output, remaining_chunk)

            # Copy the audio data into the output buffer.
            if samples_to_copy > 0:
                chunk_slice = self.current_audio_chunk[self.chunk_position : self.chunk_position + samples_to_copy]
                # The shape of outdata is (frames, channels). We assign our mono data to the first channel.
                outdata[samples_filled : samples_filled + samples_to_copy, 0] = chunk_slice
                
                # Advance our positions.
                samples_filled += samples_to_copy
                self.chunk_position += samples_to_copy

                # If we've copied the entire chunk, reset to grab a new one.
                if self.chunk_position >= len(self.current_audio_chunk):
                    self.current_audio_chunk = None
                    self.chunk_position = 0
        
        # If the loop finished before filling the buffer, the rest is silence.
        if samples_filled < frames:
            outdata[samples_filled:, 0] = 0


    async def run(self) -> None:
        """The main entry point for the demo. Sets up and runs the session."""
        print("Connecting to agent, this may take a few seconds...")

        # Initialize and start the audio player. The `callback` is key for real-time output.
        # The blocksize is set to match our audio chunk size for better synchronization.
        chunk_size = int(SAMPLE_RATE * CHUNK_LENGTH_S)
        self.audio_player = sd.OutputStream(
            channels=CHANNELS,
            samplerate=SAMPLE_RATE,
            dtype=FORMAT,
            callback=self._output_callback,
            blocksize=0,
        )
        self.audio_player.start()

        try:
            # RealtimeRunner manages the connection and session lifecycle.
            runner = RealtimeRunner(agent)
            
            # The 'async with' block handles session setup and teardown gracefully.
            async with await runner.run() as session:
                self.session = session
                print("Connection successful. Starting audio recording...")

                # Start capturing audio from the microphone.
                await self.start_audio_recording()
                print("Audio recording started. You can start speaking now.")

                # This is the main event loop. It will listen for and process events
                # from the agent session until the session is closed.
                async for event in session:
                    await self._on_event(event)

        finally:
            # Ensure the audio player is properly stopped and closed on exit.
            if self.audio_player and self.audio_player.active:
                self.audio_player.stop()
            if self.audio_player:
                self.audio_player.close()
            print("Session ended.")

    async def start_audio_recording(self) -> None:
        """Sets up and starts the microphone input stream."""
        self.audio_stream = sd.InputStream(
            channels=CHANNELS, samplerate=SAMPLE_RATE, dtype=FORMAT
        )
        self.audio_stream.start()
        self.recording = True

        # Start the audio capture loop as a separate asynchronous task.
        asyncio.create_task(self.capture_audio())

    async def capture_audio(self) -> None:
        """
        Continuously captures audio from the microphone, chunks it, and sends it
        to the agent's session for processing.
        """
        if not self.audio_stream or not self.session:
            return

        read_size = int(SAMPLE_RATE * CHUNK_LENGTH_S)

        try:
            while self.recording:
                # Wait until there are enough samples available to read.
                if self.audio_stream.read_available < read_size:
                    await asyncio.sleep(0.01) # Sleep briefly to avoid busy-waiting.
                    continue

                # Read a chunk of audio from the microphone stream.
                data, _ = self.audio_stream.read(read_size)

                # Convert the NumPy array of audio samples into raw bytes.
                audio_bytes = data.tobytes()

                # Send the audio bytes to the agent session over the network.
                await self.session.send_audio(audio_bytes)

        except Exception as e:
            print(f"Audio capture error: {e}")
        finally:
            # Clean up the audio stream when the loop exits.
            if self.audio_stream and self.audio_stream.active:
                self.audio_stream.stop()
            if self.audio_stream:
                self.audio_stream.close()

    async def _on_event(self, event: RealtimeSessionEvent) -> None:
        """
        Handles and logs events received from the RealtimeSession.
        This provides a real-time view into the agent's state.
        """
        try:
            # Use pattern matching (or if/elif chain) to handle different event types.
            if event.type == "agent_start":
                print(f"Agent started: {event.agent.name}")
            elif event.type == "agent_end":
                print(f"Agent ended: {event.agent.name}")
            elif event.type == "tool_start":
                print(f"Tool started: {event.tool.name}")
            elif event.type == "tool_end":
                print(f"Tool ended: {event.tool.name}; output: {_truncate_str(str(event.output), 100)}")
            elif event.type == "audio_end":
                print("--- Agent finished speaking ---")
            elif event.type == "audio_interrupted":
                print("--- Agent speech interrupted ---")
                # Signal the output callback to clear its queue.
                self.interrupt_event.set()
            elif event.type == "error":
                print(f"An error occurred: {event.error}")
            elif event.type == "audio":
                # This is an incoming audio chunk from the agent.
                # Convert the raw bytes back to a NumPy array.
                np_audio = np.frombuffer(event.audio.data, dtype=np.int16)
                try:
                    # Add the audio chunk to the playback queue.
                    self.output_queue.put_nowait(np_audio)
                except queue.Full:
                    # The queue is full, indicating a potential problem where audio
                    # is arriving faster than it can be played. We'll drop this chunk.
                    print("Warning: Audio output queue is full. Dropping an audio chunk.")
            # Note: We are ignoring 'history_updated', 'history_added', etc. for cleaner logs.

        except Exception as e:
            print(f"Error processing event: {e}")


# --- Script Execution ---
if __name__ == "__main__":


    print("Querying for audio devices...")
    print(sd.query_devices())


    # Create an instance of our demo class.
    demo = NoUIDemo()
    try:
        # Start the asyncio event loop and run our main demo method.
        asyncio.run(demo.run())
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully.
        print("\nExiting application...")
        sys.exit(0)