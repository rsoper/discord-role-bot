import os
import discord
import emoji
import json
import asyncio
from threading import Thread
from flask import Flask, request, render_template, redirect

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
intents = discord.Intents.all()
client = discord.Client(intents=intents)
botActivity = discord.Game("with the API")
configFileLocation = os.path.join(
    os.path.dirname(__file__), "config/config.json")
app = Flask(__name__)


def interpret_emoji(payload):
    """
    Handle logic from both add/remove emoji reacts here. DRY you idiot.
    """
    if payload.emoji.is_custom_emoji():
        emoji_name = f":{payload.emoji.name}:"
    else:
        emoji_name = emoji.demojize(payload.emoji.name)

    role_ID = get_role_ID(emoji_name)

    for role in roles:
        if role_ID == role.id:
            return role

    return None


def eligible_for_action(payload):
    user = client.get_user(payload.user_id)
    # If the user reacting is the bot, return
    if user == client.user:
        return False
    # If the reaction is not on the correct message for manging roles, return.
    # Defined in config/config.json
    if get_message_id() != payload.message_id:
        return False
    return True


def map_emoji_ids():
    """
    Match Emoji ID's from the server with emojis in the config
    """
    with open(configFileLocation, "r") as settingsFile:
        settingsData = json.load(settingsFile)
        configuredRoles = settingsData["roles"]

    for item in configuredRoles:
        if item["react_id"] == 0:
            for custom_emoji in client.emojis:
                if custom_emoji.name in item["react"]:
                    item["react_id"] = custom_emoji.id
        else:
            continue

    settingsData["roles"] = configuredRoles

    with open(configFileLocation, "w") as configFile:
        json.dump(settingsData, configFile, indent=4)


def role_message_exists():
    """
    Determine if a role message has been saved to the config

    Return Bool
    """
    with open(configFileLocation, "r") as configFile:
        configData = json.load(configFile)
        message_id = configData["role_message_id"]
    if message_id == 0:
        return False
    else:
        return True


def get_message_id():
    """
    Retreive the message ID saved in the config file

    Return Int(message_id)
    """
    with open(configFileLocation, "r") as configFile:
        configData = json.load(configFile)
        message_id = configData["role_message_id"]
    return message_id


def store_message_id(message_id):
    with open(configFileLocation, "r") as configFile:
        configData = json.load(configFile)

    configData["role_message_id"] = message_id
    with open(configFileLocation, "w") as configFile:
        json.dump(configData, configFile, indent=4)


def get_role_ID(react):
    react = emoji.demojize(react)
    with open(configFileLocation, "r") as configFile:
        configData = json.load(configFile)
        configuredRoles = configData["roles"]
    for item in configuredRoles:
        if item["react"] == react:
            return item["role_id"]


def map_role_ID(roles):
    """
    Match Role ID's from the server with Role names in the config

    roles = [Role objects]
    """
    with open(configFileLocation, "r") as settingsFile:
        settingsData = json.load(settingsFile)
        configuredRoles = settingsData["roles"]

    for item in configuredRoles:
        if item["role_id"] == 0:
            for role in roles:
                if role.name == item["role"]:
                    item["role_id"] = role.id
        else:
            continue

    settingsData["roles"] = configuredRoles

    with open(configFileLocation, "w") as configFile:
        json.dump(settingsData, configFile, indent=4)


def build_message():
    """
    Build the multi-line message combining reactions and descriptions
    from the config. 

    Return str(finalMessage)
    """
    finalMessage = """\n"""
    messageLines = []
    with open(configFileLocation) as settingsFile:
        settingsData = json.load(settingsFile)
        configuredRoles = settingsData["roles"]

    for item in configuredRoles:
        react = item["react"]
        for custom_emoji in client.emojis:
            if custom_emoji.name in react:
                react = f"<{item['react']}{item['react_id']}>"
        roleDescription = item["description"]
        messageLines.append(f"React {react} {roleDescription}")

    return finalMessage.join(messageLines)


def get_all_reacts():
    """
    Get all the reaction names from the config file

    Return [reacts]
    """
    reacts = []
    with open(configFileLocation) as settingsFile:
        settingsData = json.load(settingsFile)
        configuredRoles = settingsData["roles"]

    for item in configuredRoles:
        if item["react_id"] != 0:
            reacts.append(f"<{item['react']}{item['react_id']}>")
        else:
            reacts.append(item["react"])

    return reacts


@client.event
async def on_raw_reaction_add(payload):
    if eligible_for_action(payload):
        role = interpret_emoji(payload)
        if role == None:
            return
        await payload.member.add_roles(role)
        print(
            f"The user {payload.member} was added to the role {role.name}")


@client.event
async def on_raw_reaction_remove(payload):
    if eligible_for_action(payload):
        role = interpret_emoji(payload)
        if role == None:
            return
        for member in client.get_all_members():
            if member.id == payload.user_id:
                user = member
        await user.remove_roles(role)
        print(
            f"The user {user.name} was removed from the role {role.name}")


@client.event
async def on_ready():
    global roles, roleMessage
    # Set bot status in the server
    await client.change_presence(activity=botActivity)
    channel = await client.fetch_channel(channel_id=CHANNEL_ID)
    roles = await client.guilds[0].fetch_roles()
    map_role_ID(roles)
    map_emoji_ids()

    if role_message_exists():
        roleMessage = await channel.fetch_message(get_message_id())
        await roleMessage.edit(content=build_message())
    else:
        roleMessage = await channel.send(content=build_message())
        store_message_id(roleMessage.id)

    # Remove all reactions from the bot on the message.
    for react in roleMessage.reactions:
        await react.remove(client.user)

    # Add a reaction from the bot for each in the config
    default_reacts = get_all_reacts()
    for react in default_reacts:
        await roleMessage.add_reaction(emoji.emojize(react, use_aliases=True))


# Running Flask and Discord.py through the magic of Threading.
# Going to separate that down here for sanity sake

def read_config():
    with open(configFileLocation, "r") as settingsFile:
        settingsData = json.load(settingsFile)
        configuredRoles = settingsData["roles"]

        return configuredRoles


def write_config(formData):
    with open(configFileLocation, "r") as settingsFile:
        settingsData = json.load(settingsFile)
        roleData = settingsData["roles"]

    for key, value in formData:
        splitKey = key.split("-")
        if splitKey[1] == "react":
            for role in roleData:
                if role["role_id"] == int(splitKey[0]):
                    role["react"] = value
        elif splitKey[1] == "description":
            for role in roleData:
                if role["role_id"] == int(splitKey[0]):
                    role["description"] = value

    settingsData["roles"] = roleData

    with open(configFileLocation, "w") as settingsFile:
        json.dump(settingsData, settingsFile, indent=4)


@app.route("/save", methods=["POST", "GET"])
def save_changes():
    if request.method != "POST":
        return redirect("/")

    config_data = request.form.items()
    write_config(config_data)
    return redirect("/")


@app.route("/")
def admin_index():
    return render_template("admin.html", existing_config=read_config())


@app.route("/edit")
def edit_config():
    return render_template("edit.html", existing_config=read_config())


def admin_portal():
    app.run()


# Create an Async event loop as the method to start discord.py
loop = asyncio.get_event_loop()
loop.create_task(client.start(TOKEN))

# Create and start the Flask app thread
admin_portal_thread = Thread(target=admin_portal)
admin_portal_thread.start()

# Create and start the Discord.py loop thread. It has to be done in this order.
# I'd be lying if I said I knew why.
discord_bot_thread = Thread(target=loop.run_forever())
discord_bot_thread.start()
