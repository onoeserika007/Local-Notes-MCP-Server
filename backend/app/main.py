"""
FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import init_db
from app.api.routes import notes, ai, obsidian, search, semantic_search
from app.services.obsidian_service import ObsidianService
from app.services.file_watcher import FileWatcherService

# 全局文件监控服务
file_watcher: FileWatcherService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    Startup: Initialize database and file watcher
    Shutdown: Cleanup resources
    """
    global file_watcher
    
    # Startup
    print("🚀 Starting application...")
    await init_db()
    print("✅ Database initialized")
    
    # 启动文件监控（如果配置了 Obsidian vault 路径）
    if settings.OBSIDIAN_VAULT_PATH:
        obsidian_service = ObsidianService(settings.OBSIDIAN_VAULT_PATH)
        file_watcher = FileWatcherService(settings.OBSIDIAN_VAULT_PATH, obsidian_service)
        
        # 先执行全量同步（扫描现有文件）
        print("🔍 Performing initial sync...")
        await file_watcher.sync_all_notes()
        print("✅ Initial sync completed")
        
        # 启动实时监控
        file_watcher.start()
        print(f"✅ File watcher started for: {settings.OBSIDIAN_VAULT_PATH}")
    else:
        print("⚠️  OBSIDIAN_VAULT_PATH not configured, file watcher disabled")
    
    yield
    
    # Shutdown
    print("👋 Shutting down application...")
    if file_watcher:
        file_watcher.stop()
        print("✅ File watcher stopped")


# Create FastAPI app
app = FastAPI(
    title="AI Notes API",
    description="Backend API for AI-powered note-taking application",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
print(f"🔧 CORS Origins: {settings.cors_origins_list}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(notes.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(obsidian.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(semantic_search.router, prefix="/api/search", tags=["search"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Notes API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD
    )
