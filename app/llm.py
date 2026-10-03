from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# Option A: Gemini 2.0 Flash (Recommended — fast, highly capable, fits free tier limits)
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

# Option B: Gemini 2.0 Flash Lite (Lightweight, higher rate limits)
# llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite")

# Option C: Gemini 2.5 Flash (Upgraded reasoning & speed performance)
# llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")