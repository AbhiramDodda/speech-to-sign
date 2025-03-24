from fastapi import FastAPI, WebSocket
import whisper
import asyncio
import json
import os

app = FastAPI()

# Load Whisper Model
model = whisper.load_model("base")

# ASL Video Mapping (Modify with actual videos)
SIGN_VIDEO_MAPPING = {
    "hello": "hello.mp4",
    "thank": "thank_you.mp4",
    "yes": "yes.mp4",
    "no": "no.mp4"
}

# Active WebSocket connections
connections = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.add(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "offer":
                print("WebRTC connection started")

            elif message["type"] == "audio_chunk":
                audio_chunk = message["audio"]
                text = transcribe_audio(audio_chunk)
                video_url = map_text_to_asl_video(text)

                response = json.dumps({"text": text, "video_url": video_url})
                await websocket.send_text(response)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        connections.remove(websocket)


def transcribe_audio(audio_chunk):
    """Process incoming audio and return transcribed text"""
    # Save audio chunk temporarily
    audio_path = "temp_audio.wav"
    with open(audio_path, "wb") as f:
        f.write(audio_chunk)

    # Transcribe speech to text
    result = model.transcribe(audio_path)
    return result["text"].lower()


def map_text_to_asl_video(text):
    """Finds the ASL video matching spoken words"""
    for word, video in SIGN_VIDEO_MAPPING.items():
        if word in text:
            return f"/get_video/{video}"
    return "/get_video/default.mp4"


@app.get("/get_video/{filename}")
async def get_video(filename: str):
    """Send ASL video file to client"""
    video_path = f"sign_videos/{filename}"
    if os.path.exists(video_path):
        return FileResponse(video_path)
    return {"error": "Video not found"}
