from pydantic import BaseModel
import streamlit as st
import requests
import json
import base64
from PIL import Image, ImageDraw, ImageFont
import io

def add_text_to_image(image_data, top_text, bottom_text):
    # Load the image
    image = Image.open(io.BytesIO(image_data))
    
    # Choose a font and size
    font_size = image.width // 20
    font = ImageFont.truetype('arial.ttf', font_size)  # Using a default font 'arial.ttf'
    
    # Initialize ImageDraw
    draw = ImageDraw.Draw(image)

    # Function to draw text with a black stroke
    def draw_text_with_stroke(position, text, font, stroke_width):
        x, y = position
        # Draw stroke
        for angle in range(0, 360, 15):  # Draw the stroke in all directions
            dx = stroke_width * math.cos(math.radians(angle))
            dy = stroke_width * math.sin(math.radians(angle))
            draw.text((x+dx, y+dy), text, font=font, fill="black")
        # Draw main text
        draw.text(position, text, font=font, fill="white")

    # Calculate text length and positions
    top_text_length = draw.textlength(top_text, font=font)
    bottom_text_length = draw.textlength(bottom_text, font=font)
    top_text_position = ((image.width - top_text_length) / 2, 10)
    bottom_text_position = ((image.width - bottom_text_length) / 2, image.height - font_size * 2)

    # Add text with stroke to image
    stroke_width = 2  # Adjust the stroke width as needed
    draw_text_with_stroke(top_text_position, top_text, font, stroke_width)
    draw_text_with_stroke(bottom_text_position, bottom_text, font, stroke_width)
    return image
# Streamlit app title
st.title("Meme Generator")


OPENAI_API_KEY = ''
# File uploader for the image
image = st.file_uploader("Upload your image", type=["jpg", "png", "jpeg"])
OPENAI_API_KEY = st.text_input("OpenAI API Key")

class Meme(BaseModel):
    top_caption: str
    bottom_caption: str
    
def parse_meme_response(response):
    response= response.json()
    # Assuming response is a dictionary obtained from the API call
    content = response['choices'][0]['message']['content']
    # Find the indices for the first '{' and the last '}'
    start_index = content.find('{')
    end_index = content.rfind('}') + 1  # Include the '}' in the slice
    
    # Extract only the JSON string
    json_str = content[start_index:end_index]
    # Extract the JSON string and convert it into a dictionary
    meme_data = json.loads(json_str)
    
    # Create a Meme object from the dictionary
    meme = Meme(**meme_data)
    
    return meme
instructions = '''
YOur job is to generate a meme with top and bottom text.
you are given an image. Analyze, find what's funny in it. return two captions top and bottom.
The captions should be extremely hillarious and witty
Your answer should be ONLY a json object that validates with this:
class Meme(BaseModel):
    top_caption: str
    bottom_caption: str
'''
def generate_captions(image):
    image_data = image.read()

    # Encode the bytes to a base64 string
    base64_image = base64.b64encode(image_data).decode('utf-8')

    # Calculate the size of the base64 encoded string in bytes
    size_in_bytes = (len(base64_image) * 3) / 4 - base64_image.count('=', -2)
    print(f"Size of base64 image in bytes: {size_in_bytes}")
    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    payload = {
    "model": "gpt-4-vision-preview",
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": instructions
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
            }
        ]
        }
    ],
    'temperature': 0,
    "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    return response
# Button to generate meme
if st.button("Generate Meme"):
    try:
        if OPENAI_API_KEY == "":
            raise Exception("Please enter your OpenAI API key")
        if image is None:
            raise Exception("Please upload an image")
        response = generate_captions(image)
        meme = parse_meme_response(response)
        # Read image data
        image.seek(0)

        image_data = image.read()

        # Add text to image
        final_image = add_text_to_image(image_data, meme.top_caption, meme.bottom_caption)

        # Display the final image
        st.image(final_image)
    except Exception as e:
        st.write(e)