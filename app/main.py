from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import route modules
from app.routes.user_routes import router as user_router
from app.routes.char_routes import router as chart_router

# Create FastAPI app instance
app = FastAPI()

# Configure CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Register routers with the FastAPI app
app.include_router(user_router, prefix="/users", tags=["users"])  
app.include_router(chart_router, prefix="/chart", tags=["chart"])  
