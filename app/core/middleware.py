from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import json
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for JWT token validation"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)
        
        # Extract token from header
        token = self._extract_token(request)
        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"}
            )
        
        # Validate token (simplified for demo)
        if not self._validate_token(token):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token"}
            )
        
        # Add user info to request state
        request.state.user = self._decode_token(token)
        
        return await call_next(request)
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public"""
        public_paths = [
            "/",
            "/health",
            "/api/docs",
            "/api/redoc",
            "/openapi.json",
            "/static",
            "/web/login",
            "/api/v1/auth/login",
            "/api/v1/auth/register"
        ]
        return any(path.startswith(public_path) for public_path in public_paths)
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request headers"""
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ")[1]
        return None
    
    def _validate_token(self, token: str) -> bool:
        """Validate JWT token (simplified)"""
        # TODO: Implement proper JWT validation
        return len(token) > 10
    
    def _decode_token(self, token: str) -> dict:
        """Decode JWT token (simplified)"""
        # TODO: Implement proper JWT decoding
        return {"user_id": "demo_user", "role": "admin"}


class AuditMiddleware(BaseHTTPMiddleware):
    """Audit logging middleware for all requests"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        await self._log_request(request)
        
        # Process request
        response = await call_next(request)
        
        # Log response
        await self._log_response(request, response, start_time)
        
        return response
    
    async def _log_request(self, request: Request):
        """Log incoming request details"""
        try:
            user_id = getattr(request.state, 'user', {}).get('user_id', 'anonymous')
            log_data = {
                "timestamp": time.time(),
                "method": request.method,
                "url": str(request.url),
                "user_id": user_id,
                "ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "type": "request"
            }
            
            # Log request body for non-GET requests
            if request.method != "GET":
                try:
                    body = await request.body()
                    if body:
                        log_data["body_size"] = len(body)
                except Exception:
                    pass
            
            logger.info(f"AUDIT_REQUEST: {json.dumps(log_data)}")
            
        except Exception as e:
            logger.error(f"Failed to log request: {e}")
    
    async def _log_response(self, request: Request, response: Response, start_time: float):
        """Log response details"""
        try:
            user_id = getattr(request.state, 'user', {}).get('user_id', 'anonymous')
            duration = time.time() - start_time
            
            log_data = {
                "timestamp": time.time(),
                "method": request.method,
                "url": str(request.url),
                "user_id": user_id,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "type": "response"
            }
            
            logger.info(f"AUDIT_RESPONSE: {json.dumps(log_data)}")
            
        except Exception as e:
            logger.error(f"Failed to log response: {e}")


class RBACMiddleware(BaseHTTPMiddleware):
    """Role-based access control middleware"""
    
    def __init__(self, app, role_permissions: dict = None):
        super().__init__(app)
        self.role_permissions = role_permissions or self._get_default_permissions()
    
    async def dispatch(self, request: Request, call_next):
        # Skip RBAC for public endpoints
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)
        
        # Get user role
        user = getattr(request.state, 'user', {})
        user_role = user.get('role', 'guest')
        
        # Check permissions
        if not self._has_permission(user_role, request.method, request.url.path):
            return JSONResponse(
                status_code=403,
                content={"detail": "Insufficient permissions"}
            )
        
        return await call_next(request)
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public"""
        public_paths = [
            "/",
            "/health",
            "/api/docs",
            "/api/redoc",
            "/openapi.json",
            "/static",
            "/web/login"
        ]
        return any(path.startswith(public_path) for public_path in public_paths)
    
    def _has_permission(self, role: str, method: str, path: str) -> bool:
        """Check if user has permission for the requested action"""
        if role == "admin":
            return True
        
        permissions = self.role_permissions.get(role, {})
        path_permissions = permissions.get(path, [])
        
        return method in path_permissions
    
    def _get_default_permissions(self) -> dict:
        """Get default role permissions"""
        return {
            "executive": {
                "/api/v1/projects": ["GET"],
                "/api/v1/portfolio": ["GET"],
                "/api/v1/reports": ["GET"],
                "/web/dashboard": ["GET"],
                "/web/portfolio": ["GET"]
            },
            "pm": {
                "/api/v1/projects": ["GET", "POST", "PUT"],
                "/api/v1/tasks": ["GET", "POST", "PUT"],
                "/api/v1/resources": ["GET"],
                "/web/projects": ["GET"],
                "/web/tasks": ["GET"]
            },
            "team_member": {
                "/api/v1/tasks": ["GET", "PUT"],
                "/api/v1/timesheets": ["GET", "POST", "PUT"],
                "/web/tasks": ["GET"],
                "/web/timesheets": ["GET"]
            }
        }
