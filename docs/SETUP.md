# Setup — Running Locally

## Prerequisites

- Python 3.10+
- pip
- An Anthropic (or OpenAI) API key for the agent layer
- A sample video file (or webcam) for perception testing

## 1. Clone and install

```bash
git clone <repo-url>
cd campus-safety
```

### Backend
```bash
cd backend
pip install fastapi uvicorn sqlalchemy pydantic python-dotenv anthropic
```

### Perception
```bash
cd perception
pip install ultralytics opencv-python-headless numpy requests
```

### Frontend
No build step needed if using plain HTML/JS — just open `frontend/index.html` in a
browser once the backend is running. If using React, follow standard `npm install`.

## 2. Environment variables

Create `backend/.env`:
```bash
DATABASE_URL=sqlite:///./incidents.db
ANTHROPIC_API_KEY=sk-your-key-here
```

Never commit `.env` — it's in `.gitignore`.

## 3. Run the backend

```bash
cd backend
python3 main.py
# or: uvicorn main:app --reload --port 8000
```

Verify:
```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

Visit `http://localhost:8000/docs` for the interactive API explorer.

## 4. Run the perception module

```bash
cd perception
python3 main.py
```

By default this reads from webcam (`video_path=0`). To use a sample video file, edit
the bottom of `perception/main.py`:
```python
if __name__ == "__main__":
    run("path/to/sample_video.mp4")
```

## 5. Define zones for your video

Zones are hardcoded per camera angle in `perception/zones.py`. Before testing on a new
video, redefine the polygon coordinates to match what's actually in frame — see
`docs/PERCEPTION_GUIDE.md` for how to find pixel coordinates for a zone.

## 6. Open the dashboard

Open `frontend/index.html` directly, or serve it:
```bash
cd frontend
python3 -m http.server 5500
```
Visit `http://localhost:5500`. It connects to the backend's WebSocket at
`ws://localhost:8000/ws`.

## 7. Verify end to end

1. Backend running (`localhost:8000/health` returns ok)
2. Perception running, printing "Sent {type} incident" to console when a rule fires
3. Dashboard open, showing live connection and receiving incidents as they arrive

## Troubleshooting

- **Perception can't reach backend:** check `BACKEND_URL` in `perception/config.py`
  matches where the backend is actually running.
- **Agent calls always failing/falling back:** check `ANTHROPIC_API_KEY` is set in
  `backend/.env` and the backend was restarted after adding it.
- **No detections at all:** confirm the video source actually contains people/objects
  in frame — test with `perception/test_detector.py` on a static image first.
- **Zones seem wrong:** the polygon coordinates in `zones.py` are specific to one video
  resolution/angle — redefine them per new footage.
