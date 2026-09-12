"""Run InferCache gateway as a module: python -m services.gateway"""
from services.gateway.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
