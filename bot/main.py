import os
import discord
import emoji
import json

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
intents = discord.Intents.all()
client = discord.Client(intents=intents)
botActivity = discord.Game("with the API")
configFileLocation = os.path.join(os.path.dirname(__file__), "config.json")


def role_message_exists():
    with open(configFileLocation, "r") as configFile:
        configData = json.load(configFile)
        message_id = configData["role_message_id"]
    if message_id == 0:
        return False
    else:
        return True


def get_message_id():
    with open(configFileLocation, "r") as configFile:
        configData = json.load(configFile)
        message_id = configData["role_message_id"]
    return message_id


def store_message_id(message_id):
    with open(configFileLocation, "r") as configFile:
        configData = json.load(configFile)

    configData["role_message_id"] = message_id
    with open(configFileLocation, "w") as configFile:
        json.dump(configData, configFile)


def get_role_ID(react):
    react = emoji.demojize(react)
    with open(configFileLocation, "r") as configFile:
        configData = json.load(configFile)
        configuredRoles = configData["roles"]
    for item in configuredRoles:
        if item["react"] == react:
            return item["role_id"]


def map_role_ID(roles):
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
        json.dump(settingsData, configFile)


def build_message():
    finalMessage = """\n"""
    messageLines = []
    with open(configFileLocation) as settingsFile:
        settingsData = json.load(settingsFile)
        configuredRoles = settingsData["roles"]

    for item in configuredRoles:
        react = item["react"]
        roleDescription = item["description"]
        messageLines.append(f"React {react} {roleDescription}")

    return finalMessage.join(messageLines)


def get_all_reacts():
    reacts = []
    with open(configFileLocation) as settingsFile:
        settingsData = json.load(settingsFile)
        configuredRoles = settingsData["roles"]

    for item in configuredRoles:
        reacts.append(item["react"])

    return reacts


@client.event
async def on_raw_reaction_add(payload):
    if get_message_id() != payload.message_id:
        return
    role_ID = get_role_ID(emoji.demojize(str(payload.emoji)))
    for role in roles:
        if role_ID == role.id:
            await payload.member.add_roles(role)
            print(
                f"The user {payload.member} was added to the role {role.name}")


@client.event
async def on_raw_reaction_remove(payload):
    if get_message_id() != payload.message_id:
        return
    role_ID = get_role_ID(emoji.demojize(str(payload.emoji)))
    for role in roles:
        if role_ID == role.id:
            user = client.get_user(payload.user_id)
            for member in client.get_all_members():
                if member.id == payload.user_id:
                    user = member
            await user.remove_roles(role)
            print(
                f"The user {user.name} was removed from the role {role.name}")


@client.event
async def on_reaction_add(reaction, user):
    if user == client.user:
        return
    if get_message_id() != reaction.message.id:
        return
    role_ID = get_role_ID(emoji.demojize(reaction.emoji))
    for role in roles:
        if role_ID == role.id:
            await user.add_roles(role)
            print(f"The user {user} was added to the role {role.name}")


@client.event
async def on_reaction_remove(reaction, user):
    if user == client.user:
        return
    if get_message_id() != reaction.message.id:
        return
    role_ID = get_role_ID(emoji.demojize(reaction.emoji))
    for role in roles:
        if role_ID == role.id:
            await user.remove_roles(role)
            print(f"The user {user} was removed from the role {role.name}")


@client.event
async def on_ready():
    global roles, roleMessage
    print(f"{client.user} has connected to Discord!")
    await client.change_presence(activity=botActivity)
    channel = await client.fetch_channel(channel_id=CHANNEL_ID)

    if role_message_exists():
        print("Role message exists already. Thanks!")
        roleMessage = await channel.fetch_message(get_message_id())
        await roleMessage.edit(content=build_message())
    else:
        roleMessage = await channel.send(content=build_message())
        store_message_id(roleMessage.id)

    default_reacts = get_all_reacts()

    for react in default_reacts:
        print(f"Adding {emoji.emojize(react, use_aliases=True)}")
        await roleMessage.add_reaction(emoji.emojize(react, use_aliases=True))

    roles = await client.guilds[0].fetch_roles()
    map_role_ID(roles)


client.run(TOKEN)
