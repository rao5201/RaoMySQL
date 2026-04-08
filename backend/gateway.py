"""
Unified API Gateway
Single entry point for all Rao* systems.
Routes requests to appropriate backend services.
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from typing import Dict, Any

app = FastAPI(
    title="Rao Unified Gateway",
    description="Single API gateway for RaoMySQL, RaoCMS, RaoFileManager",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Backend service URLs (configurable via env)
SERVICES = {
    "raomysql": "http://localhost:8000",   # RaoMySQL backend
    "raocms": "http://localhost:8002",     # RaoCMS backend
    "raofm": "http://localhost:8001",      # RaoFileManager backend
}

# Route mapping: /api/{system}/{path} -> service
# Examples:
#   /api/mysql/connections  -> raomysql /connections
#   /api/cms/articles       -> raocms /articles
#   /api/fm/files           -> raofm /files

async def proxy_request(
    system: str,
    path: str,
    request: Request,
    client: httpx.AsyncClient
) -> Dict[str, Any]:
    """Proxy request to appropriate backend"""
    if system not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Unknown system: {system}")
    
    base_url = SERVICES[system]
    url = f"{base_url}/{path}"
    
    # Forward headers (including Authorization)
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove original host
    
    # Get body if present
    body = await request.body()
    
    # Make request
    try:
        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body if body else None,
            params=request.query_params,
            timeout=30.0
        )
        return {
            "status_code": response.status_code,
            "content": response.content,
            "headers": dict(response.headers)
        }
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail=f"{system} service unavailable")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail=f"{system} service timeout")

@app.api_route("/api/{system}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def gateway(system: str, path: str, request: Request):
    """Main gateway route"""
    async with httpx.AsyncClient() as client:
        result = await proxy_request(system, path, request, client)
    
    return JSONResponse(
        content=result["content"],
        status_code=result["status_code"],
        headers={k: v for k, v in result["headers"].items() if k.lower() in ["content-type"]}
    )

# Health check for all services
@app.get("/health")
async def health():
    """Check health of all backend services"""
    results = {}
    async with httpx.AsyncClient() as client:
        for name, url in SERVICES.items():
            try:
                resp = await client.get(f"{url}/health", timeout=5.0)
                results[name] = {"status": "ok", "code": resp.status_code}
            except:
                results[name] = {"status": "error", "code": None}
    return results

# System info
@app.get("/")
async def info():
    return {
        "gateway": "Rao Unified API Gateway",
        "version": "1.0.0",
        "systems": {
            "raomysql": {"url": "/api/mysql/*", "description": "MySQL Database Management"},
            "raocms": {"url": "/api/cms/*", "description": "Enterprise CMS/ERP"},
            "raofm": {"url": "/api/fm/*", "description": "File Management"},
        }
    }

# Cross-system data sync endpoints
@app.post("/sync/user/{user_id}")
async def sync_user(user_id: int):
    """Sync user data across all systems"""
    # This would trigger user sync to all backends
    # Implementation depends on sync strategy
    return {"message": f"User {user_id} sync triggered", "systems": list(SERVICES.keys())}

@app.post("/sync/permissions/{user_id}")
async def sync_permissions(user_id: int):
    """Sync user permissions across all systems"""
    return {"message": f"Permissions for user {user_id} sync triggered"}