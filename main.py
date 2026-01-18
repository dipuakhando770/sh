import os, random, time, hashlib, json, re, piexif, httpx
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from io import BytesIO
from datetime import datetime

# ============ CONFIG & US DATA 2026 ============
PROGRAM_ID = "67c8c14f5f17a83b745e3f82"
SHEERID_API_URL = "https://services.sheerid.com/rest/v2"

# Universities with verified high auto-pass rates for Jan 2026
UNIVERSITIES = [
    {"id": 2565, "name": "Pennsylvania State University", "domain": "psu.edu", "weight": 100},
    {"id": 3499, "name": "University of California, Los Angeles", "domain": "ucla.edu", "weight": 98},
    {"id": 2285, "name": "New York University", "domain": "nyu.edu", "weight": 97},
    {"id": 378, "name": "Arizona State University", "domain": "asu.edu", "weight": 95},
    {"id": 3535, "name": "University of Illinois Urbana-Champaign", "domain": "illinois.edu", "weight": 92},
    {"id": 1603, "name": "Indiana University Bloomington", "domain": "iu.edu", "weight": 90}
]

# ============ FORENSIC GENERATOR ============
class ForensicEngine:
    @staticmethod
    def add_realistic_noise(img):
        arr = np.array(img).astype(np.float32)
        noise = np.random.normal(0, 8, arr.shape) # Sensor grain
        return Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8))

    @staticmethod
    def inject_metadata(buf):
        """Spoofs iPhone 15 Pro Max metadata with US GPS tags."""
        now = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
        exif_dict = {"0th": {piexif.ImageIFD.Make: u"Apple", piexif.ImageIFD.Model: u"iPhone 15 Pro Max", piexif.ImageIFD.DateTime: now},
                     "Exif": {piexif.ExifIFD.DateTimeOriginal: now},
                     "GPS": {piexif.GPSIFD.GPSLatitudeRef: 'N', piexif.GPSIFD.GPSLatitude: ((40, 1), (42, 1), (4600, 100))}}
        exif_bytes = piexif.dump(exif_dict)
        out = BytesIO()
        img = Image.open(buf)
        img.save(out, format="JPEG", exif=exif_bytes, quality=85)
        return out.getvalue()

    @staticmethod
    def create_id(name, school):
        img = Image.new("RGB", (900, 560), (240, 240, 240))
        draw = ImageDraw.Draw(img)
        # 2026 Aesthetic: Minimalist Dark Header
        draw.rectangle([0, 0, 900, 100], fill=(25, 25, 25))
        draw.text((450, 50), school.upper(), fill="white", anchor="mm")
        draw.text((100, 200), f"STUDENT: {name}", fill="black")
        draw.text((100, 280), f"VALID THRU: 05/2027", fill="black")
        
        img = ForensicEngine.add_realistic_noise(img)
        img = img.filter(ImageFilter.GaussianBlur(0.2))
        
        buf = BytesIO()
        img.save(buf, format="JPEG")
        return ForensicEngine.inject_metadata(buf)

# ============ API VERIFIER ============
class GeminiVerifier:
    def __init__(self, url):
        self.url = url
        self.vid = re.search(r"verificationId=([a-f0-9]+)", url).group(1)
        self.client = httpx.Client(timeout=30)

    def run(self):
        uni = random.choice(UNIVERSITIES)
        name = "Alex Johnson" # Example name
        print(f"[*] Targeting: {uni['name']} for {name}")
        
        # 1. Generate Doc
        doc_bytes = ForensicEngine.create_id(name, uni['name'])
        
        # 2. Upload (Simplified flow)
        payload = {"files": [{"fileName": "id.jpg", "fileSize": len(doc_bytes)}]}
        r = self.client.post(f"{SHEERID_API_URL}/verification/{self.vid}/step/docUpload", json=payload)
        upload_url = r.json()['documents'][0]['uploadUrl']
        
        print("[*] Uploading Forensic ID to S3...")
        self.client.put(upload_url, content=doc_bytes)
        
        self.client.post(f"{SHEERID_API_URL}/verification/{self.vid}/step/completeDocUpload")
        print("[+] Submission Complete. Check your email in 24h.")

if __name__ == "__main__":
    v_url = input("Enter SheerID URL: ")
    GeminiVerifier(v_url).run()
