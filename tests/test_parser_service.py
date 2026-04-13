from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.parser_service import ParserService


def test_extract_youtube_video_id_from_watch_url() -> None:
    parser = ParserService()
    video_id = parser._extract_youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert video_id == "dQw4w9WgXcQ"


def test_extract_youtube_video_id_from_short_url() -> None:
    parser = ParserService()
    video_id = parser._extract_youtube_video_id("https://youtu.be/dQw4w9WgXcQ")
    assert video_id == "dQw4w9WgXcQ"
