from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.db.session import init_db, SessionLocal
from app.models.user import User
from app.utils.enums import UserRole
import uuid

# ✅ MISSING PART 1: Import the router
from app.api.v1.issues import router as issues_router

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ MISSING PART 2: Include the router in the app
# Since your router already has prefix="/issues", this will create paths like:
# /api/v1/issues/
app.include_router(issues_router, prefix="/api/v1")

# Define a constant UUID so both Main and Issues API use the same one
DEMO_USER_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")

@app.on_event("startup")
def on_startup():
    # 1. Create Tables
    init_db()
    
    # 2. Seed Dummy User (Option A)
    db = SessionLocal()
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == DEMO_USER_ID).first()
        if not user:
            print(f"Creating Demo User with ID: {DEMO_USER_ID}")
            dummy_user = User(
                id=DEMO_USER_ID,
                email="demo@issuespotter.app",
                username="demouser",
                hashed_password="hashed_secret_password", # dummy hash
                role=UserRole.USER.value,
                is_verified=True,
                trust_score=1.0
            )
            db.add(dummy_user)
            db.commit()
            print("✅ Demo User Created")
        else:
            print("✅ Demo User already exists")
    except Exception as e:
        print(f"❌ Error seeding user: {e}")
    finally:
        db.close()

@app.get("/")
async def root():
    return {
        "message": "IssueSpotter API is running",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}