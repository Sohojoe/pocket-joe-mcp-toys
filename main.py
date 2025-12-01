"""YouTube MCP Server - Railway deployment with pocket-joe policies."""

import os
import re
import sys
import asyncio
from typing import Any

import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from fastmcp import FastMCP

from pocket_joe import BaseContext, InMemoryRunner, Message, Policy, policy_spec_mcp_tool
from pocket_joe.policy_spec_mcp import get_policy_spec


def _extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from URL."""
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None


@policy_spec_mcp_tool(description="Transcribe YouTube video to text")
class TranscribeYouTubePolicy(Policy):
    async def __call__(self, url: str) -> list[Message]:
        """
        Get video title, transcript and thumbnail from YouTube URL.
        
        :param url: YouTube video URL
        """
        video_id = _extract_video_id(url)
        if not video_id:
            return [
                Message(
                    id="",
                    actor=self.__class__.__name__,
                    type="action_result",
                    payload={"error": "Invalid YouTube URL"}
                )
            ]
        
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.find('title')
            title = title_tag.text.replace(" - YouTube", "") if title_tag else "Unknown Title"
            
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            
            ytt_api = YouTubeTranscriptApi()
            fetched_transcript = ytt_api.fetch(video_id)
            transcript = " ".join([snippet.text for snippet in fetched_transcript])
            
            return [
                Message(
                    id="",
                    actor=self.__class__.__name__,
                    type="action_result",
                    payload={
                        "title": title,
                        "transcript": transcript,
                        "thumbnail_url": thumbnail_url,
                        "video_id": video_id
                    }
                )
            ]
        except Exception as e:
            return [
                Message(
                    id="",
                    actor=self.__class__.__name__,
                    type="action_result",
                    payload={"error": str(e)}
                )
            ]


# Create FastMCP server
mcp = FastMCP("youtube-transcriber")

# Initialize pocket-joe context
runner = InMemoryRunner()
class AppContext(BaseContext):
    def __init__(self, runner):
        super().__init__(runner)
        self.transcribe_yt = self._bind(TranscribeYouTubePolicy)

ctx = AppContext(runner)


@mcp.tool()
async def transcribe_youtube(url: str) -> dict[str, Any]:
    """
    Get video title, transcript and thumbnail from YouTube URL.
    
    Args:
        url: YouTube video URL
        
    Returns:
        Dictionary containing title, transcript, thumbnail_url, and video_id
    """
    msgs = await ctx.transcribe_yt(url=url)
    
    for msg in msgs:
        if msg.type == "action_result":
            if "error" in msg.payload:
                raise RuntimeError(msg.payload["error"])
            return msg.payload
    
    return {"error": "Policy returned no result"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    is_deployment = os.getenv("PORT") is not None or os.getenv("RAILWAY_ENVIRONMENT") is not None
    is_stdio_mode = not sys.stdin.isatty() and not is_deployment
    
    if is_stdio_mode:
        # Run in stdio mode for local MCP clients
        async def run_server():
            await mcp.run_stdio_async()
        
        asyncio.run(run_server())
    else:
        # Run in HTTP mode for Railway/web deployment
        print(f"Running MCP HTTP server on port {port}")
        async def run_server():
            await mcp.run_http_async(
                host="0.0.0.0",
                port=port,
                path="/",
                log_level="debug"
            )
        
        asyncio.run(run_server())
