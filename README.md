# 🌦️ Weather Agent

An AI agent that checks the current weather using tools. Built with LangChain, Gemini, Groq and Streamlit.

**🔗 Live demo:** [weather-agent](https://weather-agent-mi7773.streamlit.app/)

Part of the [GenAI Engineer Bootcamp](https://www.udemy.com/course/ai-developer-bootcamp/), extended from a command-line script into a deployed chat app.

## Features

- Decides on its own which tools to call
- Switches from Gemini to Groq when limits are hit
- Finds your real city using browser GPS
- Shows the tool calls behind each answer

## Run locally

```bash
pip install -r requirements.txt
cp .env.example .env   # add your GOOGLE_API_KEY and GROQ_API_KEY
streamlit run app.py
```