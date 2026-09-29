# EasyOCR library for reading text from images
import easyocr

# Create OCR reader object
# 'en' = English language
reader = easyocr.Reader([
    'en',
    'hi'
])


def extract_text_from_image(image_path):
    """
    Reads text from an image and returns extracted text.
    """

    # OCR scans image
    result = reader.readtext(image_path)

    # Store extracted text
    extracted_text = "" 

    # Loop through detected text
    for item in result:

        # item[1] contains actual text
        extracted_text += item[1] + " "

    # Remove extra spaces
    extracted_text = extracted_text.strip()

    return extracted_text