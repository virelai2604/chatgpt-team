import os
import json
import numpy as np
from PIL import Image

SAMPLES = r"C:\Tools\ChatGpt Domain\Cloudflare\chatgpt-team\samples files"
os.makedirs(SAMPLES, exist_ok=True)

# Make sure pydub uses the correct ffmpeg
try:
    from pydub.utils import which
    from pydub import AudioSegment
    AudioSegment.converter = which("ffmpeg")
    PYDUB_OK = True
except ImportError:
    PYDUB_OK = False

def make_text():
    path = os.path.join(SAMPLES, "sample.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("This is a BIFL relay sample text file.\n")
    print(f"✅ Created: {path}")

def make_json():
    path = os.path.join(SAMPLES, "sample.json")
    data = {
        "type": "bifl-sample",
        "message": "Hello, OpenAI Relay!",
        "value": 1234,
        "list": [1, 2, 3]
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Created: {path}")

def make_image():
    path = os.path.join(SAMPLES, "sample.png")
    arr = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    img.save(path)
    print(f"✅ Created: {path}")

def make_mp3():
    path = os.path.join(SAMPLES, "sample.mp3")
    if PYDUB_OK:
        try:
            import wave
            import struct
            wav_path = path.replace(".mp3", ".wav")
            with wave.open(wav_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(44100)
                duration_sec = 1
                frames = [struct.pack('<h', 0) for _ in range(44100 * duration_sec)]
                wf.writeframes(b"".join(frames))
            AudioSegment.from_wav(wav_path).export(path, format="mp3")
            os.remove(wav_path)
            print(f"✅ Created: {path}")
        except Exception as e:
            with open(path, "wb") as f:
                f.write(b"FAKE MP3 FILE FOR BIFL TEST")
            print(f"⚠️  Created placeholder (not a real MP3): {path} ({e})")
    else:
        with open(path, "wb") as f:
            f.write(b"FAKE MP3 FILE FOR BIFL TEST")
        print(f"⚠️  Created placeholder (pydub not installed): {path}")

def make_pdf():
    try:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="BIFL Test PDF File", ln=1)
        path = os.path.join(SAMPLES, "sample.pdf")
        pdf.output(path)
        print(f"✅ Created: {path}")
    except ImportError:
        path = os.path.join(SAMPLES, "sample.pdf")
        with open(path, "wb") as f:
            f.write(b"FAKE PDF FILE FOR BIFL TEST")
        print(f"⚠️  Created placeholder (no fpdf): {path}")

def make_csv():
    path = os.path.join(SAMPLES, "sample.csv")
    with open(path, "w", encoding="utf-8") as f:
        f.write("id,name,value\n1,BIFL,42\n")
    print(f"✅ Created: {path}")

def make_all():
    make_text()
    make_json()
    make_image()
    make_mp3()
    make_pdf()
    make_csv()
    print("\n🎉 All BIFL sample files created in:\n", SAMPLES)

if __name__ == "__main__":
    make_all()
