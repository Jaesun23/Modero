import pytest
import asyncio
from domain.services.audio_service import AudioService


@pytest.mark.asyncio
async def test_audio_stream_lifecycle():
    """오디오 스트림 시작 -> 데이터 수신 -> 스트리밍 -> 종료 테스트"""
    # Given
    service = AudioService()
    user_id = "test_user_1"
    audio_chunk_1 = b"chunk1"
    audio_chunk_2 = b"chunk2"

    # When: 스트림 시작 및 데이터 푸시
    await service.start_stream(user_id)
    await service.push_audio(user_id, audio_chunk_1)
    await service.push_audio(user_id, audio_chunk_2)

    # 비동기로 종료 신호를 보냄 (소비자가 데이터를 다 읽은 후 종료되도록)
    async def stop_later():
        await asyncio.sleep(0.1)
        await service.stop_stream(user_id)

    asyncio.create_task(stop_later())

    # Then: 스트림 소비 검증
    received_data = []
    async for chunk in service.get_audio_stream(user_id):
        received_data.append(chunk)

    assert received_data == [audio_chunk_1, audio_chunk_2]
    # 스트림 종료 후 큐가 정리되었는지 확인 (구현 방식에 따라 다를 수 있음, 여기서는 메모리 해제 확인용)
    assert user_id not in service._queues


@pytest.mark.asyncio
async def test_push_to_non_existent_stream():
    """존재하지 않는 스트림에 푸시할 경우 에러 없이 무시되는지(또는 핸들링되는지) 확인"""
    service = AudioService()
    # 시작하지 않은 유저에게 푸시
    await service.push_audio("unknown_user", b"data")

    # 큐가 생성되지 않았으므로 아무 일도 일어나지 않아야 함 (혹은 에러 로그)
    assert "unknown_user" not in service._queues
