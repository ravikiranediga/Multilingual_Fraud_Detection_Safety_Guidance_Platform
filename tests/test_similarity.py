from backend.services.similarity_service import find_most_similar

chunks = [
    "Never share OTP with anyone.",
    "Courier scams ask for delivery fees.",
    "Fake jobs ask for registration fees."
]

query = "Please provide verification code"

result = find_most_similar(
    query,
    chunks
)

print(result)