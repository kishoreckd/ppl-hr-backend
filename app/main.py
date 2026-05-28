from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, SessionLocal, engine
from app.core.exceptions import http_exception_handler, unhandled_exception_handler

# Import route modules
from app.routes.attendance_routes import router as attendance_router
from app.routes.admin_routes import router as admin_router
from app.routes.audit_routes import router as audit_router
from app.routes.approval_routes import router as approval_router
from app.routes.auth_routes import router as auth_router
from app.routes.employee_routes import router as employee_router
from app.routes.user_routes import router as user_router
from app.routes.char_routes import router as chart_router
from app.routes.holiday_routes import router as holiday_router
from app.routes.leave_routes import router as leave_router
from app.routes.regularization_routes import router as regularization_router
from app.services.team_pilot import seed_team_pilot

# Create FastAPI app instance
app = FastAPI(title="ppl-hr API", version="1.0.0")

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
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(employee_router, prefix="/employees", tags=["employees"])
app.include_router(attendance_router, prefix="/attendance", tags=["attendance"])
app.include_router(regularization_router, prefix="/regularization", tags=["regularization"])
app.include_router(leave_router, prefix="/leave", tags=["leave"])
app.include_router(holiday_router, prefix="/holidays", tags=["holidays"])
app.include_router(approval_router, prefix="/approvals", tags=["approvals"])
app.include_router(audit_router, prefix="/audit", tags=["audit"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])


app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


@app.on_event("startup")
def startup_seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_team_pilot(db)
    finally:
        db.close()
