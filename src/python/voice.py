"""Voice I/O stub — graceful degradation when audio libs unavailable."""


class VoiceIO:
    """Voice interface that falls back to text if audio libs are missing."""

    def __init__(self):
        self.available = False
        self.libs_loaded = []
        self._recognizer = None
        self._engine = None
        try:
            import speech_recognition as sr
            self._recognizer = sr.Recognizer()
            self.libs_loaded.append("speech_recognition")
        except ImportError:
            pass
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self.libs_loaded.append("pyttsx3")
        except (ImportError, Exception):
            pass
        self.available = len(self.libs_loaded) == 2
        if not self.available:
            missing = []
            if "speech_recognition" not in self.libs_loaded:
                missing.append("speech_recognition")
            if "pyttsx3" not in self.libs_loaded:
                missing.append("pyttsx3")
            print(f"[voice] Audio libs unavailable ({', '.join(missing)}). Using text fallback.")

    def listen(self):
        """Capture speech or fall back to text input."""
        if self.available:
            import speech_recognition as sr
            with sr.Microphone() as source:
                print("[voice] Listening...")
                audio = self._recognizer.listen(source)
            try:
                return self._recognizer.recognize_google(audio)
            except Exception as e:
                print(f"[voice] Recognition failed: {e}")
                return ""
        return input("[voice] > ")

    def speak(self, text):
        """Speak text via TTS or print as fallback."""
        if self.available and self._engine:
            self._engine.say(text)
            self._engine.runAndWait()
        else:
            print(f"[voice] {text}")

    def status(self):
        """Return voice subsystem status."""
        return {
            "available": self.available,
            "libs_loaded": self.libs_loaded,
            "mode": "audio" if self.available else "text_fallback",
        }


def simulate_conversation():
    """Simulate a voice conversation to prove the interface works."""
    print("=== Voice I/O Simulation ===")
    vio = VoiceIO()
    print(f"Status: {vio.status()}")
    prompts = ["Hello, how can I help?", "Processing your request...", "Goodbye!"]
    fake_inputs = ["Tell me the weather", "Thanks", "Bye"]
    for reply, user_input in zip(prompts, fake_inputs):
        vio.speak(reply)
        print(f"  [sim input] {user_input}")
    vio.speak("Session complete.")
    print("=== Simulation Done ===")


if __name__ == "__main__":
    simulate_conversation()
