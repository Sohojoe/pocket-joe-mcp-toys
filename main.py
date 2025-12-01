"""YouTube MCP Server - Railway deployment with pocket-joe policies."""

import os
import re
from typing import Any

import requests
import uvicorn
from bs4 import BeautifulSoup
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool
from starlette.applications import Starlette
from starlette.routing import Route
from youtube_transcript_api import YouTubeTranscriptApi

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


# Create MCP server
mcp = Server("youtube-transcriber")
class AppContext(BaseContext):
    def __init__(self, runner):
        super().__init__(runner)
        self.transcribe_yt = self._bind(TranscribeYouTubePolicy)
runner = InMemoryRunner()
ctx = AppContext(runner)


@mcp.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    spec = get_policy_spec(TranscribeYouTubePolicy)
    return [
        Tool(
            name=spec.name,
            description=spec.description,
            inputSchema=spec.input_schema
        )
    ]


@mcp.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute MCP tool by calling the corresponding policy."""
    msgs = await ctx.transcribe_yt(**arguments)
    
    for msg in msgs:
        if msg.type == "action_result":
            if "error" in msg.payload:
                raise RuntimeError(msg.payload["error"])
            return msg.payload
    
    return {"error": "Policy returned no result"}


# SSE endpoint handler
async def handle_sse(request):
    """Handle SSE transport for MCP."""
    async with SseServerTransport("/messages") as transport:
        await mcp.run(
            transport.read_stream,
            transport.write_stream,
            mcp.create_initialization_options()
        )


# Starlette app
app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
    ]
)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
