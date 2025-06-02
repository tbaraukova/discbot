# DiscBot

A Discord bot that forwards messages and files from users to a specified channel.

## Features

- Forwards private messages to a designated channel
- Supports file attachments and stickers
- Simple setup with slash commands
- Web UI for entering Discord token and monitoring bot status

## Requirements

- Python 3.8+
- Discord Bot Token

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

### Using the Web UI (Recommended)

1. Run the bot:
   ```
   python main.py
   ```

2. Open your browser and navigate to `http://localhost:8080`

3. Enter your Discord token in the web interface and click "Start Bot"

4. In Discord, use the `/set_destination` command in the channel where you want messages to be forwarded.

### Using Environment Variables (Alternative)

1. Create a `.env` file with the following variables:
   ```
   DISCORD_TOKEN=your_discord_token_here
   DATA_DIR=/path/to/data/directory  # Optional, defaults to current directory
   ```

2. Run the bot:
   ```
   python main.py
   ```

3. In Discord, use the `/set_destination` command in the channel where you want messages to be forwarded.

## Deployment Options

### Docker

1. Build the Docker image:
   ```
   docker build -t discbot .
   ```

2. Run the container:
   ```
   docker run -d --name discbot -p 8080:8080 -e DISCORD_TOKEN=your_token_here -v /path/to/data:/app/data discbot
   ```

### Docker Compose

1. Create a `.env` file with your Discord token
2. Run:
   ```
   docker-compose up -d
   ```

### Heroku

1. Create a new Heroku app
2. Set the environment variables (optional):
   ```
   heroku config:set DISCORD_TOKEN=your_token_here
   ```
3. Deploy the app:
   ```
   git push heroku main
   ```
4. Open the app in your browser and enter your Discord token if not set via environment variables

**Note**: The application uses Gunicorn as the WSGI server when deployed to Heroku. This is configured in the Procfile and requirements.txt.

## Troubleshooting

- If the bot doesn't start, check that your Discord token is correct
- If messages aren't being forwarded, make sure you've set a destination channel using `/set_destination`
- For persistent data storage, ensure the `DATA_DIR` environment variable points to a persistent storage location
- If the web UI is not accessible, check that port 8080 is not blocked by a firewall
- If you encounter a Heroku error "No web processes running", make sure the Procfile is correctly configured with `web: gunicorn main:app`

## Credits

Thanks Alex for the original idea
