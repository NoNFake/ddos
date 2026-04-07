from fastapi import FastAPI
import uvicorn

app = FastAPI()



@app.get("/")
async def root():
    return {"status": "ok", "message": "Test server is alive"}

@app.post("/")
async def post_root():
    return {"status": "ok", "received": True}

if __name__ == "__main__":
    # Запуск на порту 8080
    uvicorn.run(app, host="0.0.0.0", port=8080)