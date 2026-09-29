import os

from backend.services.chunking_service import split_text_into_chunks
from backend.services.similarity_service import find_most_similar


def get_knowledge(
    category,
    user_message
):
    """
    Load scam knowledge and retrieve
    most relevant chunk.
    """

    file_map = {
        "Banking Scam": "banking.txt",
        "OTP Scam": "otp.txt",
        "UPI Scam": "upi.txt",
        "Courier Scam": "courier.txt",
        "Job Scam": "job.txt",
        "Government Scam": "government.txt"
    }

    filename = file_map.get(category)

    if not filename:
        return "No knowledge found."

    path = os.path.join(
        "data",
        "scam_knowledge",
        filename
    )

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            content = file.read()

        # Split into chunks
        chunks = split_text_into_chunks(
            content
        )

        # Retrieve best chunk
        best_chunk = find_most_similar(
            user_message,
            chunks
        )
        print("Best Chunk:")
        print(best_chunk)

        return best_chunk

    except Exception:

        return "Knowledge file missing." 