import re
import time
from datetime import datetime
from typing import Optional, Generator, List, Dict
from urllib.parse import urlparse, parse_qs

import yt_dlp
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR, SORT_BY_RECENT

from backend.config import EXTRACT_BATCH_SIZE


VIDEO_ID_PATTERNS = [
    r"(?:youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})",
    r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
    r"(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
    r"(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
]


def extract_video_id(url: str) -> Optional[str]:
    for pattern in VIDEO_ID_PATTERNS:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None


def is_channel_url(url: str) -> bool:
    return any(x in url for x in ["/channel/", "/@", "/user/", "/c/"])


def extract_playlist_id(url: str) -> Optional[str]:
    qs = parse_qs(urlparse(url).query)
    return qs.get("list", [None])[0]


def extract_video_info(url: str) -> dict:
    """Get video metadata (title, channel, stats)."""
    opts = {"quiet": True, "no_warnings": True, "skip_download": True, "extract_flat": False}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "video_id": info.get("id"),
            "title": info.get("title"),
            "description": info.get("description"),
            "upload_date": _parse_date(info.get("upload_date")),
            "views": info.get("view_count"),
            "likes": info.get("like_count"),
            "tags": info.get("tags", []),
            "channel": info.get("channel") or info.get("uploader"),
            "channel_url": info.get("channel_url"),
        }


def _parse_date(s):
    if not s:
        return None
    try:
        if len(s) == 8:
            return datetime.strptime(s, "%Y%m%d")
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def extract_comments_batch(
    video_id: str,
    max_comments: int = 50000,
    batch_size: int = EXTRACT_BATCH_SIZE,
    sort_by: str = "popular",
) -> Generator[List[Dict], None, None]:
    """
    Generator that yields batches of comments.
    Never loads all comments into memory at once.
    """
    downloader = YoutubeCommentDownloader()
    sort = SORT_BY_POPULAR if sort_by == "popular" else SORT_BY_RECENT

    batch = []
    count = 0
    seen_ids = set()

    for comment in downloader.get_comments_from_url(
        f"https://www.youtube.com/watch?v={video_id}",
        sort_by=sort,
    ):
        cid = comment.get("cid")
        if not cid or cid in seen_ids:
            continue
        seen_ids.add(cid)

        # Parse like_count — can be string like "1.4K" or encoded garbage
        raw_votes = comment.get("votes", 0)
        try:
            raw_str = str(raw_votes).strip().replace(",", "")
            if raw_str.upper().endswith("M"):
                like_count = int(float(raw_str[:-1]) * 1_000_000)
            elif raw_str.upper().endswith("K"):
                like_count = int(float(raw_str[:-1]) * 1_000)
            else:
                like_count = int(float(raw_str))
        except (ValueError, TypeError):
            like_count = 0

        batch.append({
            "comment_id": cid,
            "video_id": video_id,
            "parent_id": comment.get("parent_id"),
            "author": comment.get("author"),
            "author_channel": comment.get("channel") or comment.get("author_channel"),
            "text_original": comment.get("text"),
            "like_count": like_count,
            # 'time' is a localised relative string (e.g. '1 year ago', '1 سال پہلے').
            # 'time_parsed' is the actual Unix timestamp provided by the library.
            "published_at": _parse_timestamp(comment.get("time_parsed") or comment.get("time")),
            "is_reply": bool(comment.get("reply")),
        })
        count += 1

        if len(batch) >= batch_size:
            yield batch
            batch = []

        if count >= max_comments:
            break

    if batch:
        yield batch


def _parse_timestamp(t):
    if isinstance(t, (int, float)):
        return datetime.fromtimestamp(t)
    if isinstance(t, str):
        try:
            return datetime.fromisoformat(t.replace("Z", "+00:00"))
        except ValueError:
            pass
    return None


def get_channel_videos(channel_url: str, max_videos: int = 50) -> list:
    opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True}
    videos = []
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)
        if "entries" in info:
            for entry in info["entries"][:max_videos]:
                if entry:
                    videos.append({
                        "video_id": entry.get("id"),
                        "title": entry.get("title"),
                        "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                        "views": entry.get("view_count"),
                    })
    return videos


def get_playlist_videos(playlist_url: str, max_videos: int = 50) -> list:
    opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True}
    videos = []
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
        if "entries" in info:
            for entry in info["entries"][:max_videos]:
                if entry:
                    videos.append({
                        "video_id": entry.get("id"),
                        "title": entry.get("title"),
                        "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                        "views": entry.get("view_count"),
                    })
    return videos
