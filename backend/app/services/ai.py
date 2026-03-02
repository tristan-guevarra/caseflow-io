# handles all the openai stuff - extraction, embeddings, chunking

import json
import re

import openai
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.prompts.extraction import (
    DOCUMENT_EXTRACTION_SYSTEM_PROMPT,
    DOCUMENT_EXTRACTION_USER_PROMPT,
    EMBEDDING_CHUNK_OVERLAP,
    EMBEDDING_CHUNK_SIZE,
)
from app.schemas.documents import AIExtractionResult

logger = structlog.get_logger()
settings = get_settings()


def get_openai_client() -> openai.OpenAI:
    return openai.OpenAI(api_key=settings.OPENAI_API_KEY)


# pull text out of pdf bytes
def extract_text_from_pdf(file_content: bytes) -> str:
    from PyPDF2 import PdfReader
    from io import BytesIO

    reader = PdfReader(BytesIO(file_content))
    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)
    return "\n\n".join(text_parts)


# pull text out of docx bytes
def extract_text_from_docx(file_content: bytes) -> str:
    from docx import Document
    from io import BytesIO

    doc = Document(BytesIO(file_content))
    return "\n\n".join(para.text for para in doc.paragraphs if para.text.strip())


# pick the right extractor based on file type
def extract_text(file_content: bytes, file_type: str) -> str:
    if file_type in ("application/pdf", "pdf"):
        return extract_text_from_pdf(file_content)
    elif file_type in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx"):
        return extract_text_from_docx(file_content)
    else:
        # just try plain text
        return file_content.decode("utf-8", errors="replace")


# strip markdown code fences from llm json responses
def _clean_json_response(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


# send the doc to openai for extraction, retries 3x on failure
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def run_extraction(document_text: str, filename: str, file_type: str) -> AIExtractionResult:
    client = get_openai_client()

    # chop it down if it's too long for the context window
    max_chars = 400_000
    truncated = document_text[:max_chars]
    if len(document_text) > max_chars:
        logger.warning("document_truncated", original_len=len(document_text), truncated_to=max_chars)

    user_prompt = DOCUMENT_EXTRACTION_USER_PROMPT.format(
        filename=filename,
        file_type=file_type,
        document_text=truncated,
    )

    logger.info("ai_extraction_started", filename=filename, text_length=len(truncated))

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": DOCUMENT_EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=4096,
        response_format={"type": "json_object"},
    )

    raw_content = response.choices[0].message.content
    if not raw_content:
        raise ValueError("Empty response from OpenAI")

    # clean up and validate the response
    cleaned = _clean_json_response(raw_content)
    parsed = json.loads(cleaned)
    result = AIExtractionResult.model_validate(parsed)

    logger.info(
        "ai_extraction_completed",
        filename=filename,
        parties=len(result.parties),
        deadlines=len(result.deadlines),
        obligations=len(result.obligations),
        risk_flags=len(result.risk_flags),
    )
    return result


# split text into overlapping chunks for embedding
def chunk_text(text: str, chunk_size: int = EMBEDDING_CHUNK_SIZE, overlap: int = EMBEDDING_CHUNK_OVERLAP) -> list[str]:
    if not text or not text.strip():
        return []

    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


# send text chunks to openai embeddings api, retries 3x
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
def generate_embeddings(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    client = get_openai_client()
    response = client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


# convenience wrapper for embedding a single string
def generate_single_embedding(text: str) -> list[float]:
    results = generate_embeddings([text])
    return results[0] if results else []
