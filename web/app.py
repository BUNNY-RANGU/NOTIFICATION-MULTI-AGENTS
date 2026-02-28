# app.py
# =====================================================
# JOB: FastAPI application entry point
# Command to run: uvicorn app:app --reload
# Then open: http://localhost:8000
# =====================================================

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from web.database import init_db
from web.routes import router, save_report_to_db, save_inventory_to_db

# Create FastAPI app
app = FastAPI(
    title="Shop AI Agent Dashboard",
    description="Multi-Agent AI system for shop owners",
    version="1.0.0"
)

# Allow all origins (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Include all routes
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Runs when app starts — initialize database."""
    print("🚀 Shop AI Dashboard starting...")
    init_db()
    print("✅ Ready! Open http://localhost:8000")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)