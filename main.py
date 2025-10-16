import os
import re
import urllib.parse
import asyncio
from pyrogram import Client, filters
import aiohttp
import ffmpeg
from dotenv import load_dotenv

# Load .env variables
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Client("render_downloader", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Start message
@bot.on_message(filters.command("start"))
async def start(_, message):
    await message.reply_text("👋 Send me your Render link and I will download the video for you!")

# Video download handler
@bot.on_message(filters.text & ~filters.command(["start"]))
async def download_video(_, message):
    url = message.text.strip()
    if "render.com" not in url:
        return await message.reply_text("❌ Invalid link. Please send a valid Render video URL.")

    status_msg = await message.reply_text("⏳ Extracting video link...")

    try:
        # Decode link
        parsed = urllib.parse.unquote(url)
        match = re.search(r"https[^&]+\.m3u8", parsed)
        if not match:
            return await status_msg.edit_text("❌ Could not extract video link.")
        m3u8_url = match.group(0)

        await status_msg.edit_text("⏳ Downloading video...")

        # Use ffmpeg to download video async
        output_file = "output.mp4"
        process = (
            ffmpeg
            .input(m3u8_url)
            .output(output_file, c="copy", loglevel="error")
            .overwrite_output()
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )

        # Wait until ffmpeg finishes
        await asyncio.to_thread(process.wait)

        await status_msg.edit_text("✅ Uploading video to Telegram...")
        await message.reply_video(output_file, caption="🎬 Download complete!")

        os.remove(output_file)
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"⚠️ Error: {e}")

bot.run()
