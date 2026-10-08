import logging

import streamlit as st
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import ModelFallbackMiddleware
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from streamlit_js_eval import get_geolocation

from tools import get_weather, reverse_geocode

logging.getLogger("langchain_google_genai").setLevel(logging.ERROR)
load_dotenv()

st.set_page_config(page_title="Weather Agent", page_icon="🌦️")
st.title("🌦️ Weather Agent")
st.caption(
    "An AI agent that checks the **current** weather (live conditions right now, not a forecast). "
    "Built with LangChain, Gemini and Groq."
)


# ---------- Location (from the user's browser, not the server) ----------

if "detected_city" not in st.session_state:
    st.session_state.detected_city = ""

with st.sidebar:
    st.header("📍 Your location")

    if not st.session_state.detected_city:
        geo = get_geolocation()  # asks the browser for permission
        if geo and "coords" in geo:
            coords = geo["coords"]
            st.session_state.detected_city = reverse_geocode(
                coords["latitude"], coords["longitude"]
            )

    user_city = st.text_input(
        "Detected automatically, or type your city:",
        value=st.session_state.detected_city,
        placeholder="e.g. Alexandria, Egypt",
    )
    st.session_state.user_city = user_city

    if st.button("🗑️ Clear chat"):
        st.session_state.messages = []
        st.rerun()


def make_get_location(city: str):
    """
    Build a get_location tool that already knows the user's city.
    The agent runs tools in a background thread where st.session_state
    can't be read, so we hand the city to the tool directly instead.
    """
    def get_location():
        """
        Get the user's current location (city, country).
        Use this when the user asks about weather without specifying a city.
        """
        return city or "Unknown. Ask the user which city they are in."

    return get_location


# ---------- Agent ----------

SYSTEM_PROMPT = """
You are a helpful weather assistant.
YOUR WORKFLOW:
1. If the user asks about weather WITHOUT specifying a location, you MUST:
   - First call get_location() to find their location
   - Then call get_weather(city) with that location
2. If the user provides a city, call get_weather(city) directly.
3. Report the condition, temperature in both Celsius and Fahrenheit,
   feels-like temperature, humidity and wind.
4. You only have CURRENT conditions, not forecasts. If the user asks about
   later today, tomorrow or any future time, say you can only give the
   current weather, then offer it.
"""


@st.cache_resource
def load_models():
    """Create the model connections once and reuse them on every rerun."""
    # No temperature set: Gemini 3 models work best at their default (1.0).
    # Lower values can make them loop or produce garbled text.
    gemini = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        max_retries=0,  # fail fast so the fallback kicks in
    )
    groq = ChatGroq(model="openai/gpt-oss-120b", temperature=0.7)
    return gemini, groq


def build_agent(city: str):
    """Build the agent with a get_location tool that knows the current city."""
    gemini, groq = load_models()
    return create_agent(
        model=gemini,
        tools=[get_weather, make_get_location(city)],
        middleware=[ModelFallbackMiddleware(groq)],
        system_prompt=SYSTEM_PROMPT,
    )


# ---------- Chat ----------

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Ask about the current weather..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        history_len = len(st.session_state.messages)
        with st.spinner("Checking the weather..."):
            try:
                agent = build_agent(user_city)
                result = agent.invoke({"messages": st.session_state.messages})
                answer = result["messages"][-1].text
                new_steps = result["messages"][history_len:]
            except Exception as e:
                answer = f"Sorry, something went wrong: {e}"
                new_steps = []

        st.markdown(answer)

        # Show what the agent did behind the scenes
        if new_steps:
            with st.expander("🔧 Agent steps"):
                model_name = new_steps[-1].response_metadata.get("model_name", "unknown")
                st.caption(f"Answered by: {model_name}")
                for msg in new_steps:
                    if msg.type == "ai" and msg.tool_calls:
                        for call in msg.tool_calls:
                            st.markdown(f"**Called** `{call['name']}` with `{call['args']}`")
                    elif msg.type == "tool":
                        st.markdown(f"**Result from** `{msg.name}`:")
                        st.code(msg.content)

    st.session_state.messages.append({"role": "assistant", "content": answer})