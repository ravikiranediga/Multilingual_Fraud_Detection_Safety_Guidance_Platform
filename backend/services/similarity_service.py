from sklearn.metrics.pairwise import cosine_similarity

from backend.services.embedding_service import generate_embedding


def find_most_similar(
    query,
    chunks
):
    """
    Find the most relevant chunk.
    """

    # User embedding
    query_embedding = generate_embedding(
        query
    )

    # Store chunk embeddings
    chunk_embeddings = []

    for chunk in chunks:

        embedding = generate_embedding(
            chunk
        )

        chunk_embeddings.append(
            embedding
        )

    # Similarity scores
    scores = cosine_similarity(
        [query_embedding],
        chunk_embeddings
    )[0]
    print(scores)
    # Highest score index
    best_index = scores.argmax()

    return chunks[best_index]