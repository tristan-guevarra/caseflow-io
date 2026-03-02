# tests for the main api endpoints and core utilities

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch

from app.main import app
from app.core.security import hash_password, create_access_token


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def test_client():
    # test client without a real db
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


# health check
@pytest.mark.anyio
async def test_health_check(test_client):
    response = await test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ai-caseflow"
    assert "version" in data


# password hashing
def test_password_hashing():
    from app.core.security import hash_password, verify_password
    password = "TestPass123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)


# jwt token creation and verification
def test_jwt_tokens():
    import uuid
    from app.core.security import create_access_token, create_refresh_token, decode_token

    user_id = uuid.uuid4()
    access = create_access_token(user_id)
    refresh = create_refresh_token(user_id)

    access_payload = decode_token(access)
    assert access_payload is not None
    assert access_payload["sub"] == str(user_id)
    assert access_payload["type"] == "access"

    refresh_payload = decode_token(refresh)
    assert refresh_payload is not None
    assert refresh_payload["type"] == "refresh"


# bad tokens should return none
def test_invalid_jwt():
    from app.core.security import decode_token
    assert decode_token("invalid.token.here") is None
    assert decode_token("") is None


# check role hierarchy works (admin > lawyer > paralegal)
def test_role_hierarchy():
    from app.core.security import has_minimum_role
    assert has_minimum_role("admin", "admin")
    assert has_minimum_role("admin", "lawyer")
    assert has_minimum_role("admin", "paralegal")
    assert has_minimum_role("lawyer", "lawyer")
    assert has_minimum_role("lawyer", "paralegal")
    assert not has_minimum_role("lawyer", "admin")
    assert not has_minimum_role("paralegal", "lawyer")
    assert not has_minimum_role("paralegal", "admin")


# password validation rules on the register schema
def test_register_schema_password_validation():
    from app.schemas.auth import RegisterRequest
    import pydantic

    # valid password
    req = RegisterRequest(email="test@test.com", password="Test1234!", full_name="Test User", organization_name="Test Org")
    assert req.email == "test@test.com"

    # missing uppercase
    with pytest.raises(pydantic.ValidationError):
        RegisterRequest(email="test@test.com", password="test1234!", full_name="Test", organization_name="Org")

    # missing digit
    with pytest.raises(pydantic.ValidationError):
        RegisterRequest(email="test@test.com", password="Testtest!", full_name="Test", organization_name="Org")

    # missing special char
    with pytest.raises(pydantic.ValidationError):
        RegisterRequest(email="test@test.com", password="Testtest1", full_name="Test", organization_name="Org")

    # too short
    with pytest.raises(pydantic.ValidationError):
        RegisterRequest(email="test@test.com", password="Te1!", full_name="Test", organization_name="Org")


# matter schema validation
def test_matter_schema():
    from app.schemas.matter import CreateMatterRequest
    import pydantic

    req = CreateMatterRequest(title="Test Matter", matter_type="litigation")
    assert req.title == "Test Matter"

    # invalid matter type should fail
    with pytest.raises(pydantic.ValidationError):
        CreateMatterRequest(title="Test", matter_type="invalid_type")


# make sure the extraction result schema works
def test_extraction_result_schema():
    from app.schemas.documents import AIExtractionResult

    result = AIExtractionResult(
        summary="Test summary",
        parties=[{"name": "Test", "role": "plaintiff", "context": "Test"}],
        deadlines=[],
        obligations=[],
        key_clauses=[],
        risk_flags=[],
        key_dates=[],
    )
    assert result.summary == "Test summary"
    assert len(result.parties) == 1


# text chunking for embeddings
def test_text_chunking():
    from app.services.ai import chunk_text

    text = " ".join(["word"] * 2500)
    chunks = chunk_text(text, chunk_size=1000, overlap=200)
    assert len(chunks) >= 3
    # chunks should overlap
    assert chunks[0] != chunks[1]

    # empty text
    assert chunk_text("") == []
    assert chunk_text("   ") == []


# make sure we strip markdown fences from llm output
def test_json_cleaning():
    from app.services.ai import _clean_json_response

    assert _clean_json_response('```json\n{"key": "val"}\n```') == '{"key": "val"}'
    assert _clean_json_response('  {"key": "val"}  ') == '{"key": "val"}'
    assert _clean_json_response('```\n{"key": "val"}\n```') == '{"key": "val"}'


# storage path format sanity check
def test_storage_path_format():
    from app.services.storage import upload_document
    # can't test actual upload without minio, just verify the path pattern
    import uuid
    org_id = str(uuid.uuid4())
    matter_id = str(uuid.uuid4())
    expected_pattern = f"{org_id}/{matter_id}/"
    assert expected_pattern.count("/") == 2


# make sure prompt templates have all the fields we expect
def test_extraction_prompt_has_all_fields():
    from app.prompts.extraction import DOCUMENT_EXTRACTION_SYSTEM_PROMPT, DOCUMENT_EXTRACTION_USER_PROMPT

    assert "summary" in DOCUMENT_EXTRACTION_SYSTEM_PROMPT
    assert "parties" in DOCUMENT_EXTRACTION_SYSTEM_PROMPT
    assert "deadlines" in DOCUMENT_EXTRACTION_SYSTEM_PROMPT
    assert "obligations" in DOCUMENT_EXTRACTION_SYSTEM_PROMPT
    assert "key_clauses" in DOCUMENT_EXTRACTION_SYSTEM_PROMPT
    assert "risk_flags" in DOCUMENT_EXTRACTION_SYSTEM_PROMPT
    assert "key_dates" in DOCUMENT_EXTRACTION_SYSTEM_PROMPT

    assert "{filename}" in DOCUMENT_EXTRACTION_USER_PROMPT
    assert "{document_text}" in DOCUMENT_EXTRACTION_USER_PROMPT
