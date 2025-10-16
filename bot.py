import os
import re
import urllib.parse
import asyncio
from pyrogram import Client, filters
import ffmpeg
from dotenv import load_dotenv
import logging

# Logging for debugging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Pyrogram v2 Client
bot = Client(
    "render_downloader",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workdir="./",  # Ensure working directory
)

# /start command handler
@bot.on_message(filters.command("start"))
async def start_command(client, message):
    logging.info(f"/start received from {message.from_user.first_name}")
    await message.reply_text(
        "👋 Hi! Send me your Render link and I will download the video for you."
    )

# Video download handler
@bot.on_message(filters.text & ~filters.command(["start"]))
async def download_video(client, message):
    url = message.text.strip()
    logging.info(f"Received link: {url}")

    if "render.com" not in url:
        await message.reply_text("❌ Invalid link. Please send a valid Render video URL.")
        return

    status_msg = await message.reply_text("⏳ Extracting video link...")

    try:
        # Decode link
        parsed = urllib.parse.unquote(url)
        match = re.search(r"https[^&]+\.m3u8", parsed)
        if not match:
            await status_msg.edit_text("❌ Could not extract video link.")
            return

        m3u8_url = match.group(0)
        logging.info(f"Extracted m3u8 URL: {m3u8_url}")
        await status_msg.edit_text("⏳ Downloading video...")

        # Download using ffmpeg
        output_file = f"video_{message.from_user.id}.mp4"
        process = (
            ffmpeg.input(m3u8_url)
            .output(output_file, c="copy", loglevel="error")
            .overwrite_output()
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )
        await asyncio.to_thread(process.wait)

        # Upload video to Telegram
        await status_msg.edit_text("✅ Uploading video to Telegram...")
        await message.reply_video(output_file, caption="🎬 Download complete!")

        # Cleanup
        os.remove(output_file)
        await status_msg.delete()

    except Exception as e:
        logging.error(f"Error: {e}")
        await status_msg.edit_text(f"⚠️ Error: {e}")


if __name__ == "__main__":
    logging.info("Bot is starting...")
    bot.run()
