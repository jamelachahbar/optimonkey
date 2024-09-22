from fastapi import FastAPI
from fastapi.responses import JSONResponse
from routers import agents  # Import the new router file
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# app.include_router(recommendations.router, prefix="/api")
# app.include_router(analysis.router, prefix="/api")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(agents.router)  # Add the new router

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)

