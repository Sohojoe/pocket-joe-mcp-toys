"""Test the YouTube transcription policy directly."""

import asyncio
import sys

from main import AppContext, InMemoryRunner


async def test_transcribe():
    """Test YouTube transcription with a sample URL."""
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://youtu.be/WbqxlfJIUHw?si=-UIt4EKIfRj8a5CU"
    
    print(f"Testing transcription for: {url}\n")
    
    runner = InMemoryRunner()
    ctx = AppContext(runner)
    
    result = await ctx.transcribe_yt(url=url)
    
    for msg in result:
        if msg.type == "action_result":
            if "error" in msg.payload:
                print(f"❌ Error: {msg.payload['error']}")
            else:
                print(f"✅ Success!")
                print(f"Title: {msg.payload['title']}")
                print(f"Video ID: {msg.payload['video_id']}")
                print(f"Thumbnail: {msg.payload['thumbnail_url']}")
                print(f"\nTranscript preview (first 500 chars):")
                print(msg.payload['transcript'][:500] + "...")


if __name__ == "__main__":
    asyncio.run(test_transcribe())
