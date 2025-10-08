# HelpDesk Bot
> A Python Telegram Bot that works as a helpdesk software.

When a client sends a support message to the bot, it forwards the message to you or your company's group and you can reply it. Replying the message makes the bot reply the client.

1. The client talks to the bot.  
![The client talks to the bot screenshot](screenshots/screenshot1.png)

2. The company receives the message and replies it.  
![The company receives the message and replies it screenshot](screenshots/screenshot2.png)

3. The client receives the answer and the process continues.  
![The client receives the answer screenshot](screenshots/screenshot3.png)

# Installation & Usage

The project source now lives in the `support-bot/` directory so it can be containerised easily. You can run it either with Docker Compose or directly with Python.

## Running with Docker Compose

1. Copy the example environment file and fill in your secrets:

```
cp support-bot/.env.template support-bot/.env
```

   Edit `support-bot/.env` and set the `TELEGRAM_TOKEN` and `GROUP_CHAT_ID` values (and optionally override any other settings).

2. Build and start the services:

```
cd support-bot
docker compose up --build
```

   Docker Compose will start both the bot service and a Redis instance. The bot container is configured to restart automatically if it stops unexpectedly.

3. To stop the services press `Ctrl+C` in the terminal running Compose and then run:

```
docker compose down
```

## Running without Docker

1. Install the Python requirements and Redis:

```
pip install -r support-bot/requirements.txt
sudo apt-get install redis-server
```

2. Set the required environment variables before starting the bot:

```
export TELEGRAM_TOKEN=your_token
export GROUP_CHAT_ID=your_group_chat_id
export REDIS_HOST=localhost  # Optional overrides
```

3. Run the redis-server:

```
redis-server
```

4. In another terminal, start the bot from the `support-bot` directory:

```
cd support-bot
python -c "from main import updater; updater.start_polling()"
```

As long as you want your bot responding, keep this running. When you want to stop, just run `updater.stop()` inside a Python shell or interrupt the process with `Ctrl+C`.

**PS:** Keep in mind that you will have to generate the locale `.mo` files.

# Contribute
Copyright (C) 2016 Júlia Rizza & licensed under MIT License
