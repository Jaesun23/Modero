import pytest
from unittest.mock import AsyncMock, MagicMock
from google.cloud import speech
from infrastructure.external.google_stt import GoogleSTTClient

# DNA 원칙: Mock을 활용하여 외부 의존성 없이 로직 검증


@pytest.mark.asyncio
async def test_stt_streaming_config_generation():
    """
    Scenario: STT 클라이언트가 올바른 설정(Config) 객체를 생성하는지 확인
    """
    # Given
    mock_client = AsyncMock()
    client = GoogleSTTClient(client=mock_client)

    # When
    streaming_config = client._create_streaming_config()

    # Then
    assert streaming_config.config.language_code == "ko-KR"
    assert (
        streaming_config.config.encoding
        == speech.RecognitionConfig.AudioEncoding.LINEAR16
    )
    assert streaming_config.config.sample_rate_hertz == 16000
    assert streaming_config.interim_results is True


@pytest.mark.asyncio
async def test_transcribe_stream_processing():
    """
    Scenario: 오디오 스트림을 받아 STT 결과를 정상적으로 파싱하여 반환하는지 확인
    """
    # Given: Mock Google Speech Client 설정
    mock_speech_client = AsyncMock()

    # Mock 응답 객체 생성 (Interim 결과와 Final 결과 시뮬레이션)
    mock_result_interim = MagicMock()
    mock_result_interim.is_final = False
    mock_result_interim.alternatives = [MagicMock(transcript="안녕")]

    mock_result_final = MagicMock()
    mock_result_final.is_final = True
    mock_result_final.alternatives = [MagicMock(transcript="안녕하세요")]

    mock_response_interim = MagicMock()
    mock_response_interim.results = [mock_result_interim]

    mock_response_final = MagicMock()
    mock_response_final.results = [mock_result_final]

    # 비동기 제너레이터로 응답 시뮬레이션
    async def response_generator():
        yield mock_response_interim
        yield mock_response_final

    mock_speech_client.streaming_recognize.return_value = response_generator()

    # 가짜 오디오 스트림
    async def mock_audio_stream():
        yield b"chunk1"
        yield b"chunk2"

    # When: 클라이언트 실행
    stt_client = GoogleSTTClient(client=mock_speech_client)
    results = []
    async for result in stt_client.transcribe(mock_audio_stream()):
        results.append(result)

    # Then: 결과 검증
    assert len(results) == 2

    # 첫 번째 결과 (Interim)
    assert results[0]["text"] == "안녕"
    assert results[0]["is_final"] is False
    assert results[0]["type"] == "interim"

    # 두 번째 결과 (Final)
    assert results[1]["text"] == "안녕하세요"
    assert results[1]["is_final"] is True
    assert results[1]["type"] == "final"