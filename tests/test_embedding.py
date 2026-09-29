from backend.services.embedding_service import generate_embedding

text = "Share OTP immediately"

embedding = generate_embedding(text)

print(type(embedding))
print(len(embedding))
print(embedding[:10])