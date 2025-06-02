# DiscBot

A Discord bot that forwards messages and files from users to a specified channel.

## Features

- Forwards private messages to a designated channel
- Supports file attachments and stickers
- Simple setup with slash commands

## Requirements

- Python 3.8+
- Discord Bot Token

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Discord token (see `.env.example`)

## Configuration

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
   docker run -d --name discbot -e DISCORD_TOKEN=your_token_here -v /path/to/data:/app/data discbot
   ```

### Docker Compose

1. Create a `.env` file with your Discord token
2. Run:
   ```
   docker-compose up -d
   ```

### Heroku

1. Create a new Heroku app
2. Set the environment variables:
   ```
   heroku config:set DISCORD_TOKEN=your_token_here
   ```
3. Deploy the app:
   ```
   git push heroku main
   ```

## Troubleshooting

- If the bot doesn't start, check that your Discord token is correct
- If messages aren't being forwarded, make sure you've set a destination channel using `/set_destination`
- For persistent data storage, ensure the `DATA_DIR` environment variable points to a persistent storage location

## Credits

Thanks Alex for the original idea
