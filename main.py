import discord
import dotenv
import json
import os
import io
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('discbot')

# Load environment variables
dotenv.load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    logger.error("DISCORD_TOKEN environment variable is not set. Please set it and try again.")
    sys.exit(1)

# Configure data directory - use environment variable or default to current directory
DATA_DIR = os.getenv('DATA_DIR', os.getcwd())
DATA_FILE = os.path.join(DATA_DIR, 'data.json')

# Initialize bot with intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = discord.Bot(intents=intents)

admin = discord.Permissions.none() + discord.Permissions.administrator
no_mentions = discord.AllowedMentions.none()
info = {}


def save_data():
    """Save bot configuration data to the configured data file."""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            json.dump(info, f, indent=4)
        logger.info(f"Configuration saved to {DATA_FILE}")
    except Exception as e:
        logger.error(f"Failed to save configuration data: {str(e)}")


def get_data():
    """Load bot configuration data from the configured data file."""
    global info
    try:
        with open(DATA_FILE, 'r') as f:
            value = json.load(f)
            if value:
                info = value
                logger.info(f"Configuration loaded from {DATA_FILE}")
    except json.decoder.JSONDecodeError:
        logger.error(f"JSONDecodeError: file data is too short or file is empty: {DATA_FILE}")
    except FileNotFoundError:
        logger.warning(f"FileNotFoundError: {DATA_FILE} not found, using default configuration")
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {str(e)}")


@bot.slash_command(name="set_destination", description="Set current channel as forwarding destination",
                   default_member_permissions=admin)
async def set_slash(ctx: discord.ApplicationContext):
    channel_id = ctx.channel_id
    info['channel_id'] = channel_id
    save_data()
# Import logging to use its built-in sanitization features
import logging

async def set_slash(ctx: discord.ApplicationContext):
    channel_id = ctx.channel_id
    info['channel_id'] = channel_id
    save_data()
    logger.info("Destination channel set to %s by %s", channel_id, ctx.author)
    await ctx.respond('This channel was set as forwarding destination')
    await ctx.respond('This channel was set as forwarding destination')


@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user}")
    logger.info(f"Bot ID: {bot.user.id}")
    logger.info(f"Connected to {len(bot.guilds)} guilds")


@bot.event
async def on_message(message: discord.Message):
    await forward(message)


async def forward(message: discord.Message):
    if message.author == bot.user:
        return
    if message.guild:
        return
    
# import html  # Used to escape HTML entities in user input for safe logging

async def forward(message: discord.Message):
    if message.author == bot.user:
        return
    if message.guild:
        return
    
    logger.info(f'Forwarding message from {html.escape(message.author.name)} (ID: {message.author.id})')
    
    attachments = message.attachments
    files = []
    
    for attachment in attachments:
        try:
            f = io.BytesIO(await attachment.read())
            file = discord.File(f, attachment.filename, description=attachment.description, spoiler=attachment.is_spoiler())
            files.append(file)
        except Exception as e:
            logger.error(f"Failed to process attachment {html.escape(attachment.filename)}: {html.escape(str(e))}")
    
    channel_id = info.get('channel_id', 0)
    channel = bot.get_channel(channel_id)
    
    if channel is not None:
        try:
            await channel.send(f'User {message.author.mention} sent: {html.escape(message.content)}',
                           allowed_mentions=no_mentions, files=files, stickers=message.stickers)
            await message.add_reaction('✅')
            logger.info(f"Message from {html.escape(message.author.name)} forwarded successfully")
        except Exception as e:
            logger.error(f"Failed to forward message: {html.escape(str(e))}")
            await message.add_reaction('❌')
            await message.reply("Failed to forward your message. Please try again later.")
    else:
        logger.warning(f"No destination channel configured, message from {html.escape(message.author.name)} not forwarded")
        await message.reply("Oops... It looks like the bot is not configured yet, so your message cannot be delivered")
    
    attachments = message.attachments
    files = []
    
    for attachment in attachments:
        try:
            f = io.BytesIO(await attachment.read())
            file = discord.File(f, attachment.filename, description=attachment.description, spoiler=attachment.is_spoiler())
            files.append(file)
        except Exception as e:
            logger.error(f"Failed to process attachment {attachment.filename}: {str(e)}")
    
    channel_id = info.get('channel_id', 0)
    channel = bot.get_channel(channel_id)
    
    if channel is not None:
        try:
            await channel.send(f'User {message.author.mention} sent: {message.content}',
                           allowed_mentions=no_mentions, files=files, stickers=message.stickers)
            await message.add_reaction('✅')
await channel.send(f'User {message.author.mention} sent: {message.content}',
                           allowed_mentions=no_mentions, files=files, stickers=message.stickers)
            await message.add_reaction('✅')
            # import html
            logger.info(f"Message from {html.escape(message.author.name)} forwarded successfully")  # Sanitize user input before logging
        except Exception as e:
            logger.error(f"Failed to forward message: {str(e)}")
            await message.add_reaction('❌')
            await message.reply("Failed to forward your message. Please try again later.")
    else:
        logger.warning(f"No destination channel configured, message from {html.escape(message.author.name)} not forwarded")
        await message.reply("Oops... It looks like the bot is not configured yet, so your message cannot be delivered")
        except Exception as e:
            logger.error(f"Failed to forward message: {str(e)}")
            await message.add_reaction('❌')
            await message.reply("Failed to forward your message. Please try again later.")
    else:
        logger.warning(f"No destination channel configured, message from {message.author.name} not forwarded")
        await message.reply("Oops... It looks like the bot is not configured yet, so your message cannot be delivered")


get_data()

try:
    logger.info("Starting Discord bot...")
    bot.run(DISCORD_TOKEN, reconnect=True)
except discord.errors.LoginFailure:
    logger.error("Invalid Discord token. Please check your DISCORD_TOKEN environment variable.")
    sys.exit(1)
except Exception as e:
    logger.error(f"Error starting bot: {str(e)}")
    sys.exit(1)