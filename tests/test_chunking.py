from backend.services.chunking_service import split_text_into_chunks

text = """
Banking scams often use fake KYC updates.

OTP scams request verification codes.

Courier scams ask for parcel fees.
"""

chunks = split_text_into_chunks(text)

print(chunks)