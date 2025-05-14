import requests
import os
import sys
from mistralai import Mistral
import base64 
from PIL import Image 
import io 

def encode_image(image_path):
    """Encode the image to base64. Converts WEBP to PNG in memory. Returns (base64_string, mime_type)."""
    try:
        file_extension = os.path.splitext(image_path)[1].lower()
        mime_type = ""

        if file_extension == '.webp':
            with Image.open(image_path) as img:
                if img.mode == 'RGBA' or img.mode == 'LA' or (img.mode == 'P' and 'transparency' in img.info):
                    img = img.convert('RGB') # Or 'RGBA' if alpha needed by API and supported
                
                byte_io = io.BytesIO()
                img.save(byte_io, format='PNG')
                image_bytes = byte_io.getvalue()
                mime_type = 'image/png'
                return base64.b64encode(image_bytes).decode('utf-8'), mime_type
        elif file_extension == '.png':
            with open(image_path, "rb") as image_file:
                mime_type = 'image/png'
                return base64.b64encode(image_file.read()).decode('utf-8'), mime_type
        elif file_extension in ['.jpg', '.jpeg']:
            with open(image_path, "rb") as image_file:
                mime_type = 'image/jpeg'
                return base64.b64encode(image_file.read()).decode('utf-8'), mime_type
        else:
            # Default for other types, attempt to read but MIME type might be generic or incorrect for specific APIs
            # For robust solution, you might want to convert other types to a standard format (e.g., PNG) too
            # or use a library to determine MIME type more accurately.
            print(f"Warning: Unsupported file extension {file_extension}. Attempting to encode directly. Specify MIME type if known.")
            with open(image_path, "rb") as image_file:
                # Generic binary stream, API might reject or misinterpret.
                # For Mistral vision, they typically expect image/jpeg, image/png, image/webp, image/gif.
                # It's safer to convert to one of these or reject unsupported types.
                # For now, let's default to 'application/octet-stream' or let it fail if API doesn't like it.
                # Better: convert to PNG as a fallback for safety if possible.
                try:
                    with Image.open(image_path) as img: # Try to open with PIL to convert to PNG
                        if img.mode == 'RGBA' or img.mode == 'LA' or (img.mode == 'P' and 'transparency' in img.info):
                             img = img.convert('RGB')
                        byte_io = io.BytesIO()
                        img.save(byte_io, format='PNG')
                        image_bytes = byte_io.getvalue()
                        mime_type = 'image/png'
                        print(f"Notice: Converted {file_extension} to PNG for encoding.")
                        return base64.b64encode(image_bytes).decode('utf-8'), mime_type
                except Exception as pil_e:
                    print(f"Could not process {file_extension} with PIL ({pil_e}), sending as raw bytes. API might not support this.")
                    # This path is risky for image APIs. Best to ensure conversion to a supported format.
                    return base64.b64encode(image_file.read()).decode('utf-8'), 'application/octet-stream' 

    except FileNotFoundError:
        print(f"Error: The file {image_path} was not found.")
        return None, None
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return None, None

# Path to your image
file_path = sys.argv[1]
api_key = os.environ["MISTRAL_API_KEY"]
client = Mistral(api_key=api_key)


def is_image(file_path):
    try:
        with Image.open(file_path) as img:
            return True
    except Exception as e:
        print(f"Error opening image {file_path}: {e}")
        return False

def is_pdf(file_path):
    try:
        with open(file_path, "rb") as f:
            return f.read().startswith(b"%PDF-")
    except Exception as e:
        print(f"Error opening PDF {file_path}: {e}")
        return False

if is_image(file_path):
    image_path = file_path

    # Getting the base64 string
    base64_image_content, image_mime_type = encode_image(image_path)

    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "image_url",
            "image_url": f"data:{image_mime_type};base64,{base64_image_content}" 
        }
    )

    #import pdb; pdb.set_trace()

    print(ocr_response)
elif is_pdf(file_path):
    pdf_path = file_path
    uploaded_pdf = client.files.upload(
        file={
            "file_name": "uploaded_file.pdf",
            "content": open(pdf_path, "rb"),
        },
        purpose="ocr"
    )
    signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)
    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": signed_url.url,
        }
    )
    print(ocr_response)
else:
    print(f"Error: The file {file_path} is not an image.")
    sys.exit(1)
