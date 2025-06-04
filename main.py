import discord
import dotenv
import json
import os
import io
import sys
import logging
import threading
import html
import uuid
import time
from pathlib import Path
from flask import Flask, render_template, render_template_string, request, redirect, url_for, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('discbot')

# Configure data directory - use environment variable or default to current directory
DATA_DIR = os.getenv('DATA_DIR', os.getcwd())
DATA_FILE = os.path.join(DATA_DIR, 'data.json')

# Load environment variables (for backward compatibility)
dotenv.load_dotenv()

# Global variables
dotenv.load_dotenv()

# Global variables
# Bot configuration and status
bot_config = {
    "info": {},  # Stores bot configuration information
    "instance": None,  # Holds the DiscordBot instance
    "thread": None,  # Holds the bot thread
    "deployment_id": str(uuid.uuid4()),  # Unique identifier for this deployment
    "status": {
        "running": False,
        "error": None,
        "deploymentId": None  # Will be set to deployment_id
    }
}

# Set the deployment ID in the status
bot_config["status"]["deploymentId"] = bot_config["deployment_id"]

# Global variables for bot instance and status
info = {}  # Stores bot configuration information
bot_instance = None
bot_thread = None
deployment_id = str(uuid.uuid4())  # Generate a UUID for this deployment
bot_status = {
    "running": False,
    "error": None,
    "deploymentId": deployment_id
}

# Variables for bot restart logic
manually_terminated = False  # Flag to track if the bot was manually stopped via GUI
last_token = None  # Store the last token used to start the bot
watchdog_thread = None  # Thread for the watchdog that monitors bot status
watchdog_interval = 60  # Check bot status every 60 seconds

class DiscordBot:
    def __init__(self, token):
        self.token = token
        self.bot = None
        self.running = False
        self.error = None
        
        # Initialize bot with intents
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        self.bot = discord.Bot(intents=intents)
        
        # Set up bot event handlers
        self.setup_bot_events()
    
    def setup_bot_events(self):
        admin = discord.Permissions.none() + discord.Permissions.administrator
        
        @self.bot.slash_command(name="set_destination", description="Set current channel as forwarding destination",
                           default_member_permissions=admin)
        async def set_slash(ctx: discord.ApplicationContext):
            channel_id = ctx.channel_id
            info['channel_id'] = channel_id
            save_data()
            logger.info("Destination channel set to %s by %s", channel_id, ctx.author)
            await ctx.respond('This channel was set as forwarding destination')
        
        @self.bot.event
        async def on_ready():
            logger.info(f"Bot logged in as {self.bot.user}")
            logger.info(f"Bot ID: {self.bot.user.id}")
            logger.info(f"Connected to {len(self.bot.guilds)} guilds")
        
        @self.bot.event
        async def on_message(message: discord.Message):
            await self.forward(message)
    
    async def forward(self, message: discord.Message):
        if message.author == self.bot.user:
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
        channel = self.bot.get_channel(channel_id)
        
        if channel is not None:
            try:
                await channel.send(f'User {message.author.mention} sent: {message.content}',
                               allowed_mentions=discord.AllowedMentions.none(), files=files, stickers=message.stickers)
                await message.add_reaction('✅')
                logger.info(f"Message from {html.escape(message.author.name)} forwarded successfully")
            except Exception as e:
                logger.error(f"Failed to forward message: {html.escape(str(e))}")
                await message.add_reaction('❌')
                await message.reply("Failed to forward your message. Please try again later.")
        else:
            logger.warning(f"No destination channel configured, message from {html.escape(message.author.name)} not forwarded")
            await message.reply("Oops... It looks like the bot is not configured yet, so your message cannot be delivered")
    
    def start(self):
        """Start the bot in a non-blocking way"""
        def run_bot():
            try:
                logger.info("Starting Discord bot...")
                self.running = True
                self.error = None
                self.bot.run(self.token, reconnect=True)
            except discord.errors.LoginFailure:
                logger.error("Invalid Discord token. Please check your token.")
                self.error = "Invalid Discord token. Please check your token."
            except Exception as e:
                logger.error(f"Error starting bot: {str(e)}")
                self.error = f"Error starting bot: {str(e)}"
            finally:
                self.running = False
                logger.info("Bot has stopped")
        
        return threading.Thread(target=run_bot)
    
    def stop(self):
        """Stop the bot"""
        if self.running and self.bot:
            logger.info("Stopping Discord bot...")
            self.bot.close()
            return True
        return False


def save_data():
    """Save bot configuration data to the configured data file."""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            # Don't save the token in the info dictionary directly
            # Instead, save it separately in a secure way
            data_to_save = info.copy()
            if last_token:
                # In a production environment, you might want to encrypt the token
                # For this implementation, we'll store it as is
                data_to_save['last_token'] = last_token
            json.dump(data_to_save, f, indent=4)
        logger.info(f"Configuration saved to {DATA_FILE}")
    except PermissionError as e:
        logger.error(f"Permission denied when saving configuration data: {str(e)}")
    except IOError as e:
        logger.error(f"I/O error occurred when saving configuration data: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error when saving configuration data: {str(e)}")


def get_data():
    """Load bot configuration data from the configured data file."""
    global info, last_token
    try:
        with open(DATA_FILE, 'r') as f:
            value = json.load(f)
            if value:
                # Extract the token if it exists
                if 'last_token' in value:
                    last_token = value.pop('last_token')
                info = value
                logger.info(f"Configuration loaded from {DATA_FILE}")
    except json.decoder.JSONDecodeError:
        logger.error(f"JSONDecodeError: file data is too short or file is empty: {DATA_FILE}")
    except FileNotFoundError:
        logger.warning(f"FileNotFoundError: {DATA_FILE} not found, using default configuration")
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {str(e)}")


# Create Flask app
app = Flask(__name__)

# Define the index.html template as a string
INDEX_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>Discord Bot Control Panel</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .container {
            background-color: #f5f5f5;
            border-radius: 5px;
            padding: 20px;
            margin-top: 20px;
        }
        .status {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            font-weight: bold;
        }
        .running {
            background-color: #d4edda;
            color: #155724;
        }
        .stopped {
            background-color: #f8d7da;
            color: #721c24;
        }
        .error {
            background-color: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        input[type="text"] {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button.stop {
            background-color: #f44336;
        }
        button:hover {
            opacity: 0.8;
        }
        .deployment-info {
            font-size: 12px;
            color: #666;
            text-align: center;
            margin-top: 20px;
            padding-top: 10px;
            border-top: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <h1>Discord Bot Control Panel</h1>
    
    <div class="container">
        <h2>Bot Status</h2>
        {% if status.running %}
            <div class="status running">Bot is RUNNING</div>
        {% else %}
            <div class="status stopped">Bot is STOPPED</div>
        {% endif %}
        
        {% if status.error %}
            <div class="error">Error: {{ status.error }}</div>
        {% endif %}
        
        {% if status.running %}
            <form action="/stop" method="post">
                <button type="submit" class="stop">Stop Bot</button>
            </form>
        {% else %}
            <h2>Start Bot</h2>
            <form action="/start" method="post">
                <label for="token">Discord Token:</label>
                <input type="password" id="token" name="token" placeholder="Enter your Discord token" required>
                <button type="submit">Start Bot</button>
            </form>
        {% endif %}
    </div>
    
    <div class="deployment-info">
        Deployment ID: {{ status.deploymentId }}
    </div>
</body>
</html>"""

# Create templates function (no longer creates files)
def create_templates():
    # This function is kept for backward compatibility
    # but no longer creates any files
    pass


# Flask routes
@app.route('/')
def index():
    global bot_status
    if bot_instance:
        bot_status["running"] = bot_instance.running
        bot_status["error"] = bot_instance.error
    return render_template_string(INDEX_HTML_TEMPLATE, status=bot_status)


@app.route('/start', methods=['POST'])
def start_bot():
    global bot_instance, bot_thread, bot_status, manually_terminated, last_token
    
    token = request.form.get('token')
    if not token:
        bot_status["error"] = "No token provided"
        return redirect(url_for('index'))
    
    # Store the token for potential restart
    last_token = token
    save_data()  # Save the token to the data file
    
    # Stop existing bot if running
    if bot_instance and bot_instance.running:
        bot_instance.stop()
        if bot_thread and bot_thread.is_alive():
            bot_thread.join(timeout=5)
    
    # Create and start new bot
    try:
        bot_instance = DiscordBot(token)
        bot_thread = bot_instance.start()
        bot_thread.daemon = True  # Make thread exit when main thread exits
        bot_thread.start()
        
        # Update status
        bot_status["running"] = True
        bot_status["error"] = None
        
        # Clear the manually terminated flag since we're starting the bot
        manually_terminated = False
        
        # Wait a bit to catch immediate errors
        import time
        time.sleep(2)
        
        # Check if bot is still running
        if not bot_instance.running:
            bot_status["error"] = bot_instance.error
    except Exception as e:
        bot_status["error"] = str(e)
    
    return redirect(url_for('index'))


@app.route('/stop', methods=['POST'])
def stop_bot():
    global bot_instance, bot_status, manually_terminated
    
    if bot_instance:
        bot_instance.stop()
        bot_status["running"] = False
        
        # Set the manually terminated flag to prevent auto-restart
        manually_terminated = True
        logger.info("Bot manually terminated via GUI")
    
    return redirect(url_for('index'))


@app.route('/status', methods=['GET'])
def get_status():
    global bot_status
    if bot_instance:
        bot_status["running"] = bot_instance.running
        bot_status["error"] = bot_instance.error
    return jsonify(bot_status)


def check_bot_status():
    """Check if the bot is running and restart it if needed."""
    global bot_instance, bot_thread, bot_status, manually_terminated, last_token
    
    # If there's no bot instance or no last token, we can't restart
    if not bot_instance or not last_token:
        return
    
    # Check if the bot is running
    if not bot_instance.running and not manually_terminated:
        logger.warning("Bot is not running and was not manually terminated. Attempting to restart...")
        
        try:
            # Stop the existing bot instance if it's still around
            if bot_instance:
                bot_instance.stop()
                if bot_thread and bot_thread.is_alive():
                    bot_thread.join(timeout=5)
            
            # Create and start a new bot instance
            bot_instance = DiscordBot(last_token)
            bot_thread = bot_instance.start()
            bot_thread.daemon = True
            bot_thread.start()
            
            # Update status
            bot_status["running"] = True
            bot_status["error"] = None
            
            logger.info("Bot restarted successfully")
            
            # Wait a bit to catch immediate errors
            time.sleep(2)
            
            # Check if bot is still running after restart
            if not bot_instance.running:
                bot_status["error"] = bot_instance.error
# Check if bot is still running after restart
            if not bot_instance.running:
                bot_status["error"] = bot_instance.error
                # import html
                logger.error(f"Bot failed to restart: {html.escape(str(bot_instance.error))}")
        except Exception as e:
            bot_status["error"] = str(e)
            # import html
            logger.error(f"Error restarting bot: {html.escape(str(e))}")
        except Exception as e:
            bot_status["error"] = str(e)
            logger.error(f"Error restarting bot: {str(e)}")


def start_watchdog():
    """Start the watchdog thread that monitors the bot status."""
    def watchdog_loop():
        while True:
            try:
                check_bot_status()
            except Exception as e:
                logger.error(f"Error in watchdog loop: {str(e)}")
            
            # Sleep for the specified interval
            time.sleep(watchdog_interval)
    
    # Create and start the watchdog thread
    watchdog = threading.Thread(target=watchdog_loop)
    watchdog.daemon = True  # Make thread exit when main thread exits
    watchdog.start()
    
    return watchdog


def main():
    # Load configuration data
    get_data()
    
    # Create templates
    create_templates()
    
    # Start the watchdog thread to monitor bot status
# Create templates
    create_templates()
    
    # Start the watchdog thread to monitor bot status
    # import threading
    watchdog_thread = start_watchdog()
    logger.info("Bot watchdog started")
    
    # Check if token is provided as environment variable (for backward compatibility)
    token = os.getenv('DISCORD_TOKEN')
    if token:
        logger.info("Discord token found in environment variables. Starting bot automatically.")
        # import threading
        bot_instance = None
        bot_thread = None
        bot_status = {"running": False}
        last_token = ""
        
        # Store the token for potential restart
        last_token = token
        save_data()
    watchdog_thread = start_watchdog()
    logger.info("Bot watchdog started")
    
    # Check if token is provided as environment variable (for backward compatibility)
    token = os.getenv('DISCORD_TOKEN')
    if token:
        logger.info("Discord token found in environment variables. Starting bot automatically.")
        global bot_instance, bot_thread, bot_status, last_token
        
        # Store the token for potential restart
        last_token = token
        save_data()
        
        bot_instance = DiscordBot(token)
        bot_thread = bot_instance.start()
        bot_thread.daemon = True
        bot_thread.start()
        
        # Update status
        bot_status["running"] = True
    
    # Start Flask app
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)), debug=False)


if __name__ == '__main__':
    main()