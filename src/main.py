from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.rooms import router as rooms_router
from api.routes.websocket import router as websocket_router
from core.logging import configure_logging, get_logger

# 로깅 설정 초기화
configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="AI Moderator Backend",
    description="Real-time meeting moderation and transcription service.",
    version="0.1.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React 개발 서버 (create-react-app)
        "http://localhost:5173",  # Vite 개발 서버
        # TODO: 실제 배포 환경의 프론트엔드 도메인 추가
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 포함
app.include_router(rooms_router, prefix="/api/v1")
app.include_router(websocket_router) # WebSocket 라우터는 /ws/audio/{room_id} 경로에 있음

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup event triggered.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown event triggered.")

