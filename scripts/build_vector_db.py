import os

from backend.services.chunking_service import (
    split_text_into_chunks
)

from backend.services.faiss_service import (
    add_chunks_to_index
)

folder = "data/scam_knowledge"

all_chunks = []

for file in os.listdir(folder):

    path = os.path.join(
        folder,
        file
    )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        content = f.read()

    chunks = split_text_into_chunks(
        content
    )

    all_chunks.extend(
        chunks
    )

add_chunks_to_index(
    all_chunks
)

print(
    f"Stored {len(all_chunks)} chunks"
)