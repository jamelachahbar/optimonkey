from fastapi import FastAPI
from routers.agents import router as agents_router  # Import the router from agents
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
# Include the agents router
app.include_router(agents_router)
# app.include_router(recommendations.router, prefix="/api")
# app.include_router(analysis.router, prefix="/api")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("your_app:app", host="0.0.0.0", port=8000, ws_ping_interval=30, ws_ping_timeout=60)

