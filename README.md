# pocket-joe-mcp-toys

MCP servers built with [pocket-joe](https://github.com/Sohojoe/pocket-joe) - YouTube transcription and more.

## What's Inside

### YouTube Transcriber

MCP server that transcribes YouTube videos, extracting:
- Video title
- Full transcript
- Thumbnail URL
- Video ID

Built using `pocket-joe` policies and deployed to Railway.

## Deploy to Railway

### Prerequisites

- [Railway account](https://railway.app) (Hobby plan recommended)
- GitHub account

### Steps

1. **Push this repo to GitHub**
   ```bash
   cd pocket-joe-mcp-toys
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/pocket-joe-mcp-toys.git
   git push -u origin main
   ```

2. **Deploy to Railway**
   - Go to [Railway Dashboard](https://railway.app/dashboard)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select `pocket-joe-mcp-toys`
   - Railway auto-detects Python and deploys
   - Wait for deployment (takes ~2-3 minutes)

3. **Get your endpoint**
   - Click on your deployment
   - Copy the public URL: `https://your-app.railway.app`

## Use in Claude Desktop

Add to your Claude Desktop config at `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "youtube": {
      "url": "https://your-app.railway.app/sse"
    }
  }
}
```

Restart Claude Desktop and you'll see the YouTube transcription tool available.

## Local Development

### Setup with uv

```bash
# Install uv if you haven't
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/YOUR_USERNAME/pocket-joe-mcp-toys.git
cd pocket-joe-mcp-toys
uv sync

# Run locally
uv run python main.py
```

Server runs at `http://localhost:8000/sse`

### Test locally with Claude Desktop

Use `http://localhost:8000/sse` in your config during development.

## Architecture

This uses `pocket-joe`'s policy system:
- **Policy**: `TranscribeYouTubePolicy` - handles video transcription
- **MCP Adapter**: Wraps policy as MCP tool
- **Transport**: SSE (Server-Sent Events) for Railway
- **Deployment**: Stateless (scales horizontally)

## Railway Configuration

- **Runtime**: Python 3.12
- **Package Manager**: uv (auto-detected)
- **Entry Point**: `Procfile` → `python main.py`
- **Port**: Auto-assigned via `$PORT` env var

## Cost

Railway Hobby plan:
- $5/month credit
- Enough for ~500k requests/month
- Auto-sleep after inactivity (free tier)
- Custom domains included

## Adding More Tools

To add more pocket-joe policies as MCP tools:

1. Import your policy in `main.py`
2. Add to the `list_tools()` function
3. Update `call_tool()` to route by name
4. Push to GitHub (Railway auto-deploys)

## License

MIT
