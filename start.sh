#!/bin/bash
exec uvicorn services.gateway.main:app --host 0.0.0.0 --port "${GATEWAY_PORT:-8080}"
