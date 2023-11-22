from pyrogram import Client, filters
import asyncio
import logging
import os
from dotenv import load_dotenv
import json
import re

load_dotenv('config.env', override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_SESSION = os.getenv("USER_SESSION")


with open("chat_list.json", "r") as json_file:
    CHANNEL_MAPPING = json.load(json_file)


if USER_SESSION:
    app = Client(
        "my_user_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=USER_SESSION,
    )
    logger.info("Bot started using Session String")
else:
    app = Client(
        "my_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN
    )
    logger.info("Bot started using Bot Token")

def extract_links_and_media(message):
    links = []
    media = None
    
    if message.text:
        links.extend(extract_links(message.text))
    
    if message.media:
        media = message.media
    
    return links, media

def is_supported_photo_format(file_name):
    supported_formats = ['.jpg', '.jpeg', '.png', '.gif']
    return any(file_name.lower().endswith(format) for format in supported_formats)

@app.on_message(filters.channel)
async def forward(client, message):
    
    try:
        for mapping in CHANNEL_MAPPING:
            source_channel = mapping["source"]
            destinations = mapping["destinations"]
            prefix = mapping.get("prefix", "")
            suffix = mapping.get("suffix", "")

            if message.chat.id == int(source_channel):
                source_message = await client.get_messages(int(source_channel), message.id)
                extracted_links, media = extract_links_and_media(source_message)

                if extracted_links:
                    for link in extracted_links:
                        modified_message_text = f"{prefix} {link} {suffix}".strip()

                        for destination in destinations:
                            await client.send_message(chat_id=int(destination), text=modified_message_text)
                            await asyncio.sleep(5)

                        logger.info("Forwarded a modified message from %s to %s",
                                    source_channel, destinations)
                        
                        
                        await asyncio.sleep(1)
                
                
                if media:
                    if media.photo:
                        for destination in destinations:
                            await client.send_photo(chat_id=int(destination), photo=media.photo.file_id, caption=source_message.caption)
                            await asyncio.sleep(5)

                        logger.info("Forwarded a photo from %s to %s",
                                    source_channel, destinations)
                    
                    
                    elif media.document and is_supported_photo_format(media.document.file_name):
                        for destination in destinations:
                            await client.send_document(chat_id=int(destination), document=media.document.file_id, caption=source_message.caption)
                            await asyncio.sleep(5)

                        logger.info("Forwarded a document (photo) from %s to %s",
                                    source_channel, destinations)

    except Exception as e:
        logger.exception(e)

if __name__ == "__main__":
    app.run()
    
