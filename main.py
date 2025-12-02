#!/usr/bin/env python3
"""YouTube MCP Server - Railway deployment with pocket-joe policies."""

import os
import re

import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from fastmcp import FastMCP

from pocket_joe import BaseContext, InMemoryRunner, Message, Policy, policy_spec_mcp_tool


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

class AppContext(BaseContext):
    def __init__(self, runner):
        super().__init__(runner)
        self.transcribe_yt = self._bind(TranscribeYouTubePolicy)
runner = InMemoryRunner()
ctx = AppContext(runner)

# Create FastMCP server
mcp = FastMCP("pocket-joe-mcp-toys")

# TODO: figure out a better mapping strategy to pocket-joe policies
@mcp.tool()
async def transcribe_yt(url: str) -> list[Message]:
    """
    Get video title, transcript and thumbnail from YouTube URL.
    
    :param url: YouTube video URL
    """
    return await ctx.transcribe_yt(url)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    mcp.run(transport="http", host="0.0.0.0", port=port)