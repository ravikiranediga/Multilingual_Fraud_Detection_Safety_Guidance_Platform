from backend.services.faiss_service import (
    add_chunks_to_index,
    search_chunks
)

chunks = [
    "OTP scams steal one time passwords.",
    "Courier scams ask delivery fees.",
    "Job scams ask registration fees."
]

add_chunks_to_index(
    chunks
)

result = search_chunks(
    "Share your OTP"
)

print(result)