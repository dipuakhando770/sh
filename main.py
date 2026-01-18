import sys
import re
import time
import httpx
from io import BytesIO
from core.generator import IDGenerator

# SheerID API URL 2026
SHEERID_API_URL = "https://services.sheerid.com/rest/v2"

class SheerIDVerifier:
    def __init__(self, url):
        self.url = url
        self.vid = self._extract_vid(url)
        self.client = httpx.Client(timeout=30)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/json"
        }

    def _extract_vid(self, url):
        match = re.search(r"verificationId=([a-f0-9]+)", url)
        return match.group(1) if match else None

    def skip_sso(self):
        """গুরুত্বপূর্ণ ধাপ: ইউনিভার্সিটি পোর্টাল লগইন এড়ানো"""
        print("[*] Skipping SSO login step...")
        try:
            self.client.delete(f"{SHEERID_API_URL}/verification/{self.vid}/step/sso")
        except:
            pass

    def upload_doc(self, img_bytes):
        """ডকুমেন্ট সরাসরি SheerID S3 সার্ভারে আপলোড করা"""
        print("[*] Requesting document upload URL...")
        payload = {
            "files": [{"fileName": "student_id.jpg", "mimeType": "image/jpeg", "fileSize": len(img_bytes)}]
        }
        
        # Step 1: Get Upload Link
        resp = self.client.post(f"{SHEERID_API_URL}/verification/{self.vid}/step/docUpload", json=payload)
        upload_data = resp.json()
        
        if 'documents' not in upload_data:
            print("[-] Error: Could not get upload URL.")
            return False

        upload_url = upload_data['documents'][0]['uploadUrl']
        
        # Step 2: Upload to S3
        print("[*] Uploading image to SheerID secure storage...")
        self.client.put(upload_url, content=img_bytes, headers={"Content-Type": "image/jpeg"})
        
        # Step 3: Complete Step
        print("[*] Finalizing document upload...")
        self.client.post(f"{SHEERID_API_URL}/verification/{self.vid}/step/completeDocUpload")
        return True

def main():
    print("\n--- S2 GEMINI VERIFIER 2026 UPDATE ---")
    url = input("Enter SheerID URL: ").strip()
    
    if not "verificationId=" in url:
        print("[-] Invalid URL! Please copy the full link.")
        return

    name = input("Enter Student Name: ")
    school = input("Enter University (US/UK/BD): ")

    # ১. আপনার core/generator ব্যবহার করে আইডি তৈরি
    print("[*] Creating realistic Student ID...")
    id_gen = IDGenerator()
    img = id_gen.create_id(name, school)
    
    # ইমেজ বাইটসে রূপান্তর
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=95)
    img_bytes = buf.getvalue()

    # ২. SheerID প্রসেস শুরু
    verifier = SheerIDVerifier(url)
    
    # SSO স্কিপ করা
    verifier.skip_sso()
    
    # ডকুমেন্ট আপলোড করা
    if verifier.upload_doc(img_bytes):
        print("\n[+] SUCCESS: Verification submitted successfully!")
        print("[+] Please wait 24-48 hours for review.")
    else:
        print("\n[-] FAILED: Verification submission error.")

if __name__ == "__main__":
    main()
