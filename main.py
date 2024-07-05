import discord
import dotenv
import json
import os
import io

dotenv.load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
bot = discord.Bot()

admin = discord.Permissions.none() + discord.Permissions.administrator
no_mentions = discord.AllowedMentions.none()
info = {}


def save_data():
    with open('data.json', 'w') as f:
        json.dump(info, f, indent=4)


def get_data():
    global info
    try:
        with open('data.json', 'r') as f:
            value = json.load(f)
            if value:
                info = value
    except json.decoder.JSONDecodeError:
        print('[ERROR] JSONDecodeError: file data is too short or file is empty')
    except FileNotFoundError:
        print('[ERROR] FileNotFoundError: no data.json')


@bot.slash_command(name="set_destination", description="Set current channel as forwarding destination",
                   default_member_permissions=admin)
async def set_slash(ctx: discord.ApplicationContext):
    channel_id = ctx.channel_id
    info['channel_id'] = channel_id
    save_data()
    await ctx.respond('This channel was set as forwarding destination')


@bot.event
async def on_ready():
    print(f"[INFO ] We have logged in as {bot.user}")


@bot.event
async def on_message(message: discord.Message):
    await forward(message)


async def forward(message: discord.Message):
    if message.author == bot.user:
        return
    if message.guild:
        return
    print(f'[INFO ] Forwarding message from {message.author.name}')
    attachments = message.attachments
    files = []
    # links = []
    for attachment in attachments:
        # print(attachment.to_dict())
        # links.append(attachment.url)
        f = io.BytesIO(await attachment.read())
        file = discord.File(f, attachment.filename, description=attachment.description, spoiler=attachment.is_spoiler())
        files.append(file)
    channel_id = info.get('channel_id', 0)
    channel = bot.get_channel(channel_id)
    if channel is not None:
        # links_str = '\n'.join(links)
        await channel.send(f'User {message.author.mention} sent: {message.content}',    # \n{links_str}',
                           allowed_mentions=no_mentions, files=files, stickers=message.stickers)
        await message.add_reaction('✅')
    else:
        await message.reply("Oops... It looks like the bot is not configured yet, so your message cannot be delivered")


get_data()
bot.run(DISCORD_TOKEN)