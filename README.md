# Energy Color API Starter

This is a FastAPI starter project for calculating a past energy color using a custom 10-planet expanded planetary-hour system.

## Files
- `main.py`: API server code
- `requirements.txt`: Python package list
- `openapi.yaml`: Schema for GPT Actions

## Render settings
Build Command:
```
pip install -r requirements.txt
```

Start Command:
```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Test endpoint
After deploying, open:
```
https://YOUR-RENDER-URL.onrender.com/
```

It should return:
```
{"status":"ok","message":"Energy Color API is running."}
```

## GPT Actions
Replace this line in `openapi.yaml`:
```
https://YOUR-RENDER-URL.onrender.com
```
with your actual Render URL.
