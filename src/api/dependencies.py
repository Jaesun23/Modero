from typing import Annotated

from fastapi import Depends

from core.websocket.manager import ConnectionManager, manager as ws_manager
from domain.services.audio_service import AudioService, audio_service
from infrastructure.external.gemini_client import GeminiClient
from infrastructure.external.google_stt import GoogleSTTClient
from domain.services.meeting_orchestrator import MeetingOrchestrator


def get_connection_manager() -> ConnectionManager:
    return ws_manager


def get_audio_service() -> AudioService:
    return audio_service


def get_stt_client() -> GoogleSTTClient:
    return GoogleSTTClient()


def get_gemini_client() -> GeminiClient:
    return GeminiClient()


def get_meeting_orchestrator(
    audio_service: Annotated[AudioService, Depends(get_audio_service)],
    stt_client: Annotated[GoogleSTTClient, Depends(get_stt_client)],
    gemini_client: Annotated[GeminiClient, Depends(get_gemini_client)],
    manager: Annotated[ConnectionManager, Depends(get_connection_manager)],
) -> MeetingOrchestrator:
    return MeetingOrchestrator(audio_service, stt_client, gemini_client, manager)


# Type aliases for dependencies
ConnectionManagerDep = Annotated[ConnectionManager, Depends(get_connection_manager)]
AudioServiceDep = Annotated[AudioService, Depends(get_audio_service)]
STTClientDep = Annotated[GoogleSTTClient, Depends(get_stt_client)]
GeminiClientDep = Annotated[GeminiClient, Depends(get_gemini_client)]
MeetingOrchestratorDep = Annotated[MeetingOrchestrator, Depends(get_meeting_orchestrator)]
