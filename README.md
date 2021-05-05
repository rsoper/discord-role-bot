# discord-role-bot
A simply python based Discord bot to assign roles to users based on how they react to a message. 

# Deploy with Docker

```
docker run -d -e DISCORD_TOKEN={INSERT BOT TOKEN HERE} -e CHANNEL_ID={Insert channel ID for role management} -v PATH/TO/LOCAL/config.json:/app/config/config.json richardsoper/discord-role-bot:latest
```

# Deploy with Docker Compose

From the root of this repository simply put the Discord token and your desired channel ID into a .env file then run

```
docker-compose up -d
```

# Configuration

This configuration method is not ideal. I will be adding a flask based web UI in the future to allow for more simplistic configuration. For now all config will take place in a json file.

```json
{
    "roles": [
        {
            "react": ":money_with_wings:", // Enter the name of the emoji here. 
            "react_id": 0, // Leave this at 0 on first run. It will be updated as needed. 
            "role": "Inventory Hunter", // Enter the exact spelling of the role to apply for the emoji
            "description": "if you want notifications from Inventory Hunter", // Enter a description of the role.
            "role_id": 0 // Leave this at 0 on first run. It will be updated as needed. 
        }
    ],
    "role_message_id": 0 // Leave this at 0 on first run. It will be updated as needed. 
}
```