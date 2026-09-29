import os
import faiss
import numpy as np

from backend.services.embedding_service import generate_embedding

# Paths
INDEX_PATH = os.path.join(
    "data",
    "vector_store",
    "scam_index.faiss"
)

CHUNKS_PATH = os.path.join(
    "data",
    "vector_store",
    "chunks.npy"
)

# FAISS index
index = faiss.IndexFlatL2(384)

# Store original chunks
stored_chunks = []


def add_chunks_to_index(chunks):

    global stored_chunks

    embeddings = []

    for chunk in chunks:

        embedding = generate_embedding(
            chunk
        )

        embeddings.append(
            embedding
        )

        stored_chunks.append(
            chunk
        )

    embeddings = np.array(
        embeddings
    ).astype("float32")

    index.add(
        embeddings
    )

    save_index()


def search_chunks(
    query,
    top_k=3
):

    query_embedding = generate_embedding(
        query
    )

    query_embedding = np.array(
        [query_embedding]
    ).astype("float32")

    distances, indices = index.search(
        query_embedding,
        top_k
    )

    results = []

    for idx in indices[0]:

        if idx < len(stored_chunks):

            results.append(
                stored_chunks[idx]
            )

    return results


def save_index():

    os.makedirs(
        "data/vector_store",
        exist_ok=True
    )

    faiss.write_index(
        index,
        INDEX_PATH
    )

    np.save(
        CHUNKS_PATH,
        np.array(stored_chunks)
    )

    print("FAISS index saved")


def load_index():

    global index
    global stored_chunks

    if os.path.exists(INDEX_PATH):

        index = faiss.read_index(
            INDEX_PATH
        )

        stored_chunks = np.load(
            CHUNKS_PATH,
            allow_pickle=True
        ).tolist()

        print("FAISS index loaded")