
import os
import logging

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY is missing. Add it to your .env file."
    )


PRIMARY_MODEL = os.getenv(
    "GEMINI_FAST_MODEL",
    "gemini-3.5-flash-lite",
)

FALLBACK_MODEL = os.getenv(
    "GEMINI_ADVANCED_MODEL",
    "gemini-3.1-flash-lite",
)


primary_llm = ChatGoogleGenerativeAI(
    model=PRIMARY_MODEL,
    max_retries=1,
)

fallback_llm = ChatGoogleGenerativeAI(
    model=FALLBACK_MODEL,
    max_retries=1,
)

# Use this chain in workflow nodes.
llm = primary_llm.with_fallbacks([fallback_llm])

logger.info("Primary LLM configured: %s", PRIMARY_MODEL)
logger.info("Fallback LLM configured: %s", FALLBACK_MODEL)
