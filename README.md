# discord-role-bot
A simply python based Discord bot to assign roles to users based on how they react to a message. 

# Deploy with Docker

```
docker run -d -e DISCORD_TOKEN={INSERT BOT TOKEN HERE} -e CHANNEL_ID={Insert channel ID for role management} -v PATH/TO/LOCAL/config.json:/app/config.json richardsoper/discord-role-bot:latest
```