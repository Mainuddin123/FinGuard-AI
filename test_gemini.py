from src.llm import fallback_llm

response = fallback_llm.invoke(
    "Reply with: FinGuard AI fallback connected successfully."
)

print("Response:", response.content)
print("Model metadata:", response.response_metadata)