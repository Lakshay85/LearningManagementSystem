from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from jose import jwt, JWTError
import os

from app.config import settings

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Skip auth for health checks, swagger/openapi docs, and public endpoints
        public_prefixes = ["/health", "/api", "/docs", "/openapi.json", "/v1/rag/health"]
        if any(path == prefix or path.startswith(prefix) for prefix in public_prefixes):
            return await call_next(request)

        # 1. Try JWT authentication (Bearer token forwarded from LMS)
        auth_header = request.headers.get("Authorization")
        user = None
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                # Decode using the LMS JWT access secret
                payload = jwt.decode(
                    token,
                    settings.JWT_ACCESS_SECRET,
                    algorithms=["HS256"]
                )
                user = {
                    "sub": payload.get("sub"),
                    "email": payload.get("email"),
                    "role": payload.get("role")
                }
            except JWTError as e:
                print(f"⚠️ JWT verification failed: {str(e)}")

        # 2. Try API key authentication (direct client access)
        if not user:
            api_key = request.headers.get("x-api-key")
            expected_key = settings.RAG_API_KEY

            if expected_key and api_key == expected_key:
                user = {
                    "sub": "00000000-0000-0000-0000-000000000000",
                    "email": "system@lms.local",
                    "role": "system"
                }
            elif not expected_key:
                # If no API key is configured (dev mode), log warning and bypass auth
                print("⚠️ No authentication configured - allowing request")
                user = {
                    "sub": "00000000-0000-0000-0000-000000000000",
                    "email": "dev@lms.local",
                    "role": "admin"
                }

        # Set user in request state if authenticated
        if user:
            request.state.user = user
            return await call_next(request)

        # Return 401 Unauthorized
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "statusCode": 401,
                "message": "Invalid or missing authentication"
            }
        )
