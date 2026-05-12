"""
SAMBI — Smart Assistant Made By SMNB Intelligence
Voice Assistant  ·  v2.0  ·  © SMNB
"""

import datetime
import threading
import webbrowser

import pyjokes
import pyttsx3
import pywhatkit
import requests
import speech_recognition as sr
import tkinter as tk
import wikipedia
from tkinter import scrolledtext

# ─────────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────────
WAKE_WORD = "sambi"
AI_NAME   = "SAMBI"
VERSION   = "2.0"

# ─────────────────────────────────────────────────────────────
#  COLOUR PALETTE  (GitHub-dark inspired)
# ─────────────────────────────────────────────────────────────
BG      = "#0d1117"
BG2     = "#161b22"
BG3     = "#21262d"
ACCENT  = "#58a6ff"
GREEN   = "#3fb950"
AMBER   = "#d29922"
RED     = "#f85149"
FG      = "#e6edf3"
FG2     = "#8b949e"
FG3     = "#484f58"

# ─────────────────────────────────────────────────────────────
#  TTS ENGINE
# ─────────────────────────────────────────────────────────────
engine = pyttsx3.init()
voices = engine.getProperty("voices")
if len(voices) > 1:
    engine.setProperty("voice", voices[1].id)   # female voice when available
engine.setProperty("rate",   160)
engine.setProperty("volume", 1.0)

# ─────────────────────────────────────────────────────────────
#  SPEECH RECOGNISER
# ─────────────────────────────────────────────────────────────
listener = sr.Recognizer()
listener.energy_threshold        = 3000
listener.dynamic_energy_threshold = True

# ─────────────────────────────────────────────────────────────
#  GUI — built first so helpers can reference widgets
# ─────────────────────────────────────────────────────────────
root = tk.Tk()
root.title(f"{AI_NAME}  ·  SMNB")
root.geometry("580x700")
root.configure(bg=BG)
root.resizable(False, False)

# ── Header ────────────────────────────────────────────────────
header = tk.Frame(root, bg=BG2, pady=20)
header.pack(fill=tk.X)

tk.Label(header, text=AI_NAME,
         font=("Courier New", 36, "bold"), bg=BG2, fg=ACCENT).pack()
tk.Label(header, text=f"Intelligent Voice Assistant  ·  SMNB  ·  v{VERSION}",
         font=("Courier New", 9), bg=BG2, fg=FG2).pack(pady=(2, 0))

tk.Frame(root, bg=BG3, height=1).pack(fill=tk.X)

# ── Chat log ──────────────────────────────────────────────────
chat_frame = tk.Frame(root, bg=BG, padx=14, pady=10)
chat_frame.pack(fill=tk.BOTH, expand=True)

chat_box = scrolledtext.ScrolledText(
    chat_frame, state=tk.DISABLED, wrap=tk.WORD,
    bg=BG2, fg=FG, font=("Courier New", 11),
    bd=0, padx=12, pady=12, relief=tk.FLAT,
    selectbackground=BG3,
)
chat_box.pack(fill=tk.BOTH, expand=True)

# ── Status bar ────────────────────────────────────────────────
tk.Frame(root, bg=BG3, height=1).pack(fill=tk.X)
status_var   = tk.StringVar(value=f"💤  Ready — say '{WAKE_WORD}' or click SPEAK")
status_label = tk.Label(root, textvariable=status_var,
                        font=("Courier New", 10), bg=BG, fg=FG2, pady=7)
status_label.pack()

# ── Mic button ────────────────────────────────────────────────
btn_frame = tk.Frame(root, bg=BG, pady=14)
btn_frame.pack()

mic_btn = tk.Button(
    btn_frame, text="🎙  SPEAK",
    font=("Courier New", 13, "bold"),
    bg=ACCENT, fg=BG,
    activebackground="#79c0ff", activeforeground=BG,
    relief=tk.FLAT, padx=36, pady=11,
    cursor="hand2", bd=0,
)
mic_btn.pack()

# ── Footer ────────────────────────────────────────────────────
tk.Label(root, text=f"SAMBI v{VERSION}  ·  © SMNB",
         font=("Courier New", 8), bg=BG, fg=FG3).pack(pady=(0, 10))


# ─────────────────────────────────────────────────────────────
#  GUI HELPERS  (thread-safe via root.after)
# ─────────────────────────────────────────────────────────────
def _log(speaker, text, spk_color):
    chat_box.config(state=tk.NORMAL)
    tag = f"spk_{speaker}"
    chat_box.tag_config(tag,   foreground=spk_color, font=("Courier New", 11, "bold"))
    chat_box.tag_config("msg", foreground=FG,        font=("Courier New", 11))
    chat_box.insert(tk.END, f"{speaker}\n", tag)
    chat_box.insert(tk.END, f"{text}\n\n", "msg")
    chat_box.config(state=tk.DISABLED)
    chat_box.see(tk.END)


def log(speaker, text, color=None):
    c = color or (ACCENT if speaker == AI_NAME else GREEN)
    root.after(0, _log, speaker, text, c)


def set_status(text, color=FG2):
    root.after(0, lambda: status_var.set(text))
    root.after(0, lambda: status_label.config(foreground=color))


def set_btn(enabled: bool):
    root.after(0, lambda: mic_btn.config(
        state=tk.NORMAL if enabled else tk.DISABLED,
        bg=ACCENT if enabled else BG3,
    ))


# ─────────────────────────────────────────────────────────────
#  CORE: TTS
# ─────────────────────────────────────────────────────────────
def talk(text: str):
    log(AI_NAME, text)
    engine.say(text)
    engine.runAndWait()


# ─────────────────────────────────────────────────────────────
#  CORE: WEATHER  (wttr.in — no API key required)
# ─────────────────────────────────────────────────────────────
def get_weather(city: str) -> str:
    city = city.strip() or "London"
    try:
        res = requests.get(f"https://wttr.in/{city}?format=j1", timeout=7)
        res.raise_for_status()
        d       = res.json()["current_condition"][0]
        temp    = d["temp_C"]
        feels   = d["FeelsLikeC"]
        desc    = d["weatherDesc"][0]["value"]
        humidity = d["humidity"]
        wind    = d["windspeedKmph"]
        return (f"In {city.title()}: {desc}. "
                f"Temperature {temp}°C, feels like {feels}°C. "
                f"Humidity {humidity}%, wind {wind} km/h.")
    except requests.exceptions.ConnectionError:
        return "I can't reach the weather service. Please check your internet connection."
    except requests.exceptions.Timeout:
        return "The weather request timed out. Please try again."
    except (KeyError, ValueError):
        return f"I received unexpected data for '{city}'. Try a different city name."
    except Exception as e:
        return f"An error occurred fetching weather: {e}"


# ─────────────────────────────────────────────────────────────
#  CORE: OPEN WEBSITES
# ─────────────────────────────────────────────────────────────
WEBSITES: dict[str, str] = {
    "youtube":   "https://youtube.com",
    "google":    "https://google.com",
    "github":    "https://github.com",
    "wikipedia": "https://wikipedia.org",
    "reddit":    "https://reddit.com",
    "twitter":   "https://twitter.com",
    "x":         "https://x.com",
    "instagram": "https://instagram.com",
    "facebook":  "https://facebook.com",
    "netflix":   "https://netflix.com",
    "spotify":   "https://open.spotify.com",
    "gmail":     "https://mail.google.com",
    "maps":      "https://maps.google.com",
    "whatsapp":  "https://web.whatsapp.com",
    "discord":   "https://discord.com/app",
}


def open_site(command: str) -> str:
    for name, url in WEBSITES.items():
        if name in command:
            webbrowser.open(url)
            return f"Opening {name.capitalize()}."
    query = (command
             .replace("open", "")
             .replace("go to", "")
             .replace("launch", "")
             .replace("browse", "")
             .strip())
    if query:
        webbrowser.open(f"https://www.google.com/search?q={query}")
        return f"I don't have a direct link for that, so I've searched '{query}' in your browser."
    return "Which website would you like me to open?"


# ─────────────────────────────────────────────────────────────
#  CORE: WIKIPEDIA SEARCH
# ─────────────────────────────────────────────────────────────
def wiki_search(query: str) -> str:
    try:
        return wikipedia.summary(query.strip(), sentences=2, auto_suggest=True)
    except wikipedia.exceptions.DisambiguationError as e:
        opts = ", ".join(e.options[:4])
        return f"That topic is ambiguous. Did you mean: {opts}?"
    except wikipedia.exceptions.PageError:
        return f"I couldn't find a Wikipedia article for '{query}'."
    except Exception:
        return "I ran into an issue searching Wikipedia."


# ─────────────────────────────────────────────────────────────
#  CORE: SPEECH INPUT  (bug-fixed)
# ─────────────────────────────────────────────────────────────
def take_command() -> str:
    """Listen for a voice command. Always returns a string (empty on failure)."""
    command = ""
    try:
        with sr.Microphone() as source:
            set_status("🎙  Listening...", GREEN)
            listener.adjust_for_ambient_noise(source, duration=0.5)
            audio = listener.listen(source, timeout=6, phrase_time_limit=12)

        set_status("⚙  Processing speech...", AMBER)
        command = listener.recognize_google(audio).lower()
        log("You", command, GREEN)

    except sr.WaitTimeoutError:
        set_status("⏳  No speech detected — try again", AMBER)
    except sr.UnknownValueError:
        set_status("❓  Could not understand — please speak clearly", RED)
        talk("I didn't catch that. Could you repeat it?")
    except sr.RequestError as e:
        set_status(f"🚫  Speech service error", RED)
        talk("I'm having trouble with the speech recognition service. Check your internet.")
    except OSError:
        set_status("🎤  No microphone detected", RED)
        talk("No microphone found. Please connect one and restart.")

    return command   # always a string — never unbound


# ─────────────────────────────────────────────────────────────
#  CORE: COMMAND PROCESSING
# ─────────────────────────────────────────────────────────────
def process(command: str):
    command = command.replace(WAKE_WORD, "").strip()
    now     = datetime.datetime.now()

    # ── Empty after wake word ──────────────────────────────────
    if not command:
        talk("Yes? How can I help you?")

    # ── Greetings ──────────────────────────────────────────────
    elif any(w in command for w in ("hello", "hi", "hey", "good morning", "good afternoon", "good evening")):
        hour = now.hour
        greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
        talk(f"{greeting}. I'm {AI_NAME}, your intelligent voice assistant. What can I do for you?")

    # ── Identity ───────────────────────────────────────────────
    elif any(w in command for w in ("your name", "who are you", "what are you", "introduce yourself")):
        talk(
            f"I'm {AI_NAME} — Smart Assistant Made By SMNB Intelligence. "
            f"I can answer questions, fetch weather, play music, open websites, "
            f"tell you the time and date, search Wikipedia, and more. How can I help?"
        )

    elif "how are you" in command:
        talk("All systems are running optimally. Thank you for asking. What do you need?")

    elif any(w in command for w in ("thank you", "thanks")):
        talk("You're welcome. Is there anything else I can help you with?")

    # ── Time ───────────────────────────────────────────────────
    elif "time" in command:
        t = now.strftime("%I:%M %p")
        talk(f"The current time is {t}.")

    # ── Date ───────────────────────────────────────────────────
    elif "date" in command:
        d = now.strftime("%A, %B %d, %Y")
        talk(f"Today is {d}.")

    # ── Weather ────────────────────────────────────────────────
    elif "weather" in command:
        city = (command
                .replace("weather", "")
                .replace("what is the", "")
                .replace("what's the", "")
                .replace("in", "")
                .replace("for", "")
                .replace("today", "")
                .strip())
        city = city or "London"
        set_status("🌤  Fetching weather...", ACCENT)
        response = get_weather(city)
        talk(response)

    # ── Music ──────────────────────────────────────────────────
    elif "play" in command:
        song = command.replace("play", "").strip()
        if song:
            talk(f"Playing {song} on YouTube.")
            pywhatkit.playonyt(song)
        else:
            talk("What song or video would you like me to play?")

    # ── Open websites ──────────────────────────────────────────
    elif any(w in command for w in ("open", "go to", "launch", "browse")):
        talk(open_site(command))

    # ── Search Google ──────────────────────────────────────────
    elif any(w in command for w in ("search", "google", "look up", "find")):
        query = (command
                 .replace("search", "")
                 .replace("google", "")
                 .replace("look up", "")
                 .replace("find", "")
                 .strip())
        if query:
            webbrowser.open(f"https://www.google.com/search?q={query}")
            talk(f"Opening Google search results for '{query}'.")
        else:
            talk("What would you like me to search for?")

    # ── Wikipedia ─────────────────────────────────────────────
    elif any(w in command for w in ("who is", "what is", "tell me about", "explain", "define")):
        query = (command
                 .replace("who is", "")
                 .replace("what is", "")
                 .replace("tell me about", "")
                 .replace("explain", "")
                 .replace("define", "")
                 .strip())
        if query:
            set_status("📖  Searching Wikipedia...", ACCENT)
            talk(wiki_search(query))
        else:
            talk("What topic would you like me to look up?")

    # ── Joke ───────────────────────────────────────────────────
    elif "joke" in command:
        talk(pyjokes.get_joke())

    # ── Shutdown ───────────────────────────────────────────────
    elif any(w in command for w in ("stop", "exit", "quit", "bye", "goodbye", "shut down", "shutdown")):
        talk(f"Goodbye. {AI_NAME} shutting down. Have a great day.")
        root.after(2000, root.quit)

    # ── Fallback: Google it ───────────────────────────────────
    else:
        webbrowser.open(f"https://www.google.com/search?q={command}")
        talk(f"I'm not certain how to handle that directly, but I've opened a Google search for you.")


# ─────────────────────────────────────────────────────────────
#  MAIN LOOP  (runs in background thread)
# ─────────────────────────────────────────────────────────────
def sambi_loop():
    set_btn(False)
    command = take_command()

    if command:
        if WAKE_WORD in command:
            set_status("🤖  Processing...", ACCENT)
            process(command)
        else:
            set_status(f"💤  Say '{WAKE_WORD}' first — e.g. '{WAKE_WORD}, what time is it?'", AMBER)
            talk(f"Please say {WAKE_WORD} first, then your request.")

    set_status(f"💤  Ready — say '{WAKE_WORD}' or click SPEAK", FG2)
    set_btn(True)


def on_speak_click():
    t = threading.Thread(target=sambi_loop, daemon=True)
    t.start()


mic_btn.config(command=on_speak_click)

# ─────────────────────────────────────────────────────────────
#  STARTUP MESSAGE
# ─────────────────────────────────────────────────────────────
log(AI_NAME,
    f"Hello. I'm SAMBI — Smart Assistant Made By SMNB Intelligence.\n"
    f"Say '{WAKE_WORD}' followed by your request, or click SPEAK.\n\n"
    f"Example commands:\n"
    f"  · '{WAKE_WORD}, what's the weather in Paris?'\n"
    f"  · '{WAKE_WORD}, open YouTube'\n"
    f"  · '{WAKE_WORD}, who is Nikola Tesla?'\n"
    f"  · '{WAKE_WORD}, play lo-fi music'\n"
    f"  · '{WAKE_WORD}, tell me a joke'")

root.mainloop()
