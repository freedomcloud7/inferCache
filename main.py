"""InferCache Gateway entry point for Railway auto-detection."""
from services.gateway.main import app

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("GATEWAY_PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
