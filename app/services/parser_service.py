from __future__ import annotations

import re
import urllib.request
from pathlib import Path


class ParserService:
    def extract_text(self, source_type: str, source_uri: str | None, inline_content: str | None) -> str:
        if inline_content:
            return inline_content

        if not source_uri:
            raise ValueError("Missing source_uri for non-inline document")

        if source_type == "text":
            return self._parse_text(Path(source_uri))

        if source_type == "pdf":
            return self._parse_pdf(Path(source_uri))

        if source_type == "doc":
            return self._parse_docx(Path(source_uri))

        if source_type == "url":
            return self._parse_web_url(source_uri)

        if source_type == "youtube":
            return self._parse_youtube_transcript(source_uri)

        raise ValueError(f"Unsupported source_type: {source_type}")

    def _parse_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def _parse_pdf(self, path: Path) -> str:
        try:
            import pdfplumber

            with pdfplumber.open(str(path)) as pdf:
                text = "\n".join((page.extract_text() or "") for page in pdf.pages).strip()
                if text:
                    return text
        except ImportError:
            pass

        try:
            import fitz  # pymupdf

            doc = fitz.open(str(path))
            text = "\n".join(page.get_text("text") for page in doc).strip()
            if text:
                return text
        except ImportError as exc:
            raise ValueError("PDF support requires pdfplumber or pymupdf") from exc

        raise ValueError("No extractable text found in PDF")

    def _parse_docx(self, path: Path) -> str:
        try:
            import docx
        except ImportError as exc:  # pragma: no cover
            raise ValueError("DOCX support requires dependency: python-docx") from exc

        document = docx.Document(str(path))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
        if not text:
            raise ValueError("No extractable text found in DOCX")
        return text

    def _parse_web_url(self, source_uri: str) -> str:
        try:
            from bs4 import BeautifulSoup
        except ImportError as exc:  # pragma: no cover
            raise ValueError("Web parsing requires dependency: beautifulsoup4") from exc

        with urllib.request.urlopen(source_uri, timeout=20) as response:
            html = response.read().decode("utf-8", errors="ignore")

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        text = " ".join(soup.get_text(separator=" ").split())
        if not text:
            raise ValueError("No extractable text found in webpage")
        return text

    def _parse_youtube_transcript(self, source_uri: str) -> str:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
        except ImportError as exc:  # pragma: no cover
            raise ValueError("YouTube parsing requires dependency: youtube-transcript-api") from exc

        video_id = self._extract_youtube_video_id(source_uri)
        if not video_id:
            raise ValueError("Invalid YouTube URL")

        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join(item.get("text", "") for item in transcript).strip()
        if not text:
            raise ValueError("No transcript text available for this YouTube video")
        return text

    @staticmethod
    def _extract_youtube_video_id(url: str) -> str | None:
        patterns = [r"v=([\w-]{11})", r"youtu\.be/([\w-]{11})", r"shorts/([\w-]{11})"]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
