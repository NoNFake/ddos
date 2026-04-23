import asyncio
import hashlib
from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()


@app.get("/")
async def home():
    return {"home": "http://0.0.0.0:8080/"}


@app.get("/ping")
async def ping():
    return {"status": "ok"}



@app.get("/io-heavy")
async def io_heavy():
    await asyncio.sleep(0.5)
    return {"message": "data fetched"}


@app.post("/upload")
async def upload(request: Request):
    body = await request.body()
    return {"received_bytes": len(body)}


# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8080)