from app.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=5006,  # GEO 平台端口（避开 5001/5002/5003/5004/5005）
        reload=True
    )
