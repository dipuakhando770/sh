import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

class IDGenerator:
    @staticmethod
    def add_noise(img):
        arr = np.array(img).astype(np.float32)
        noise = np.random.normal(0, 12, arr.shape) # Simulates ISO grain
        arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)

    @staticmethod
    def create_id(name, school):
        # Create a standard ID card canvas
        img = Image.new("RGB", (700, 450), (250, 250, 250))
        draw = ImageDraw.Draw(img)
        
        # Draw branding and text
        draw.rectangle([0, 0, 700, 80], fill=(30, 60, 120)) # Header
        draw.text((350, 40), school.upper(), fill="white", anchor="mm")
        draw.text((50, 150), f"NAME: {name}", fill="black")
        draw.text((50, 200), f"ID: {random.randint(10000, 99999)}", fill="black")
        
        # Apply Realism Filters
        img = img.filter(ImageFilter.GaussianBlur(0.4)) # Soften edges
        img = IDGenerator.add_noise(img) # Add sensor grain
        return img
