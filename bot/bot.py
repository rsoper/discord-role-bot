import os
import discord
import emoji
import json


class RoleBot(discord.Client):

    async def on_ready(self):
        self.bot_activity = discord.Game("with the API")
        self.CHANNEL_ID = os.getenv("CHANNEL_ID")
        self.config_file_location = os.path.join(
            os.path.dirname(__file__), "config/config.json")

        # Set bot status in the server
        await self.change_presence(activity=self.bot_activity)
        self.channel = await self.fetch_channel(channel_id=self.CHANNEL_ID)
        self.roles = await self.guilds[0].fetch_roles()
        self.map_role_id()
        self.map_emoji_ids()

        if self.role_message_exists():
            self.role_message = await self.channel.fetch_message(self.get_message_id())
            await self.role_message.edit(content=self.build_message())
        else:
            self.role_message = await self.channel.send(content=self.build_message())
            self.store_message_id(self.role_message.id)

        # Remove all reactions from the bot on the message.
        for react in self.role_message.reactions:
            await react.remove(self.user)

        # Add a reaction from the bot for each in the config
        for react in self.get_all_reacts():
            await self.role_message.add_reaction(emoji.emojize(react, use_aliases=True))

    async def on_raw_reaction_add(self, payload):
        await self.role_message.edit(content=self.build_message())
        if self.eligible_for_action(payload):
            role = self.interpret_emoji(payload)
            if role is None:
                return
            await payload.member.add_roles(role)
            print(
                f"The user {payload.member} was added to the role {role.name}")

    async def on_raw_reaction_remove(self, payload):
        if self.eligible_for_action(payload):
            role = self.interpret_emoji(payload)
            if role is None:
                return
            for member in self.get_all_members():
                if member.id == payload.user_id:
                    user = member

            await user.remove_roles(role)
            print(
                f"The user {user.name} was removed from the role {role.name}")

    def role_message_exists(self):
        """
        Determine if a role message has been saved to the config

        Return Bool
        """
        with open(self.config_file_location, "r") as config_file:
            config_data = json.load(config_file)
            message_id = config_data["role_message_id"]
        if message_id == 0:
            return False
        else:
            return True

    def get_message_id(self):
        """
        Retreive the message ID saved in the config file

        Return Int(message_id)
        """
        with open(self.config_file_location, "r") as config_file:
            config_data = json.load(config_file)
            message_id = config_data["role_message_id"]
        return message_id

    def store_message_id(self, message_id):
        with open(self.config_file_location, "r") as config_file:
            config_data = json.load(config_file)

        config_data["role_message_id"] = message_id
        with open(self.config_file_location, "w") as config_file:
            json.dump(config_data, config_file, indent=4)

    def build_message(self):
        """
        Build the multi-line message combining reactions and descriptions
        from the config. 

        Return str(final_message)
        """
        final_message = """\n"""
        message_lines = []
        with open(self.config_file_location) as config_file:
            config_data = json.load(config_file)
            configured_roles = config_data["roles"]

        for item in configured_roles:
            react = item["react"]
            for custom_emoji in self.emojis:
                if custom_emoji.name in react:
                    react = f"<{item['react']}{item['react_id']}>"
            role_description = item["description"]
            message_lines.append(f"React {react} {role_description}")

        return final_message.join(message_lines)

    def map_role_id(self):
        """
        Match Role ID's from the server with Role names in the config
        """
        with open(self.config_file_location, "r") as config_file:
            config_data = json.load(config_file)
            configured_roles = config_data["roles"]

        for item in configured_roles:
            if item["role_id"] == 0:
                for role in self.roles:
                    if role.name == item["role"]:
                        item["role_id"] = role.id
            else:
                continue

        config_data["roles"] = configured_roles

        with open(self.config_file_location, "w") as config_file:
            json.dump(config_data, config_file, indent=4)

    def map_emoji_ids(self):
        """
        Match Emoji ID's from the server with emojis in the config
        """
        with open(self.config_file_location, "r") as config_file:
            config_data = json.load(config_file)
            configured_roles = config_data["roles"]

        for item in configured_roles:
            if item["react_id"] == 0:
                for custom_emoji in self.emojis:
                    if custom_emoji.name in item["react"]:
                        item["react_id"] = custom_emoji.id
            else:
                continue

        config_data["roles"] = configured_roles

        with open(self.config_file_location, "w") as config_file:
            json.dump(config_data, config_file, indent=4)

    def get_all_reacts(self):
        """
        Get all the reaction names from the config file

        Return [reacts]
        """
        reacts = []
        with open(self.config_file_location) as config_file:
            config_data = json.load(config_file)
            configured_roles = config_data["roles"]

        for item in configured_roles:
            if item["react_id"] != 0:
                reacts.append(f"<{item['react']}{item['react_id']}>")
            else:
                reacts.append(item["react"])

        return reacts

    def interpret_emoji(self, payload):
        """
        Handle logic from both add/remove emoji reacts here. DRY you idiot.
        """
        if payload.emoji.is_custom_emoji():
            emoji_name = f":{payload.emoji.name}:"
        else:
            emoji_name = emoji.demojize(payload.emoji.name)

        role_id = self.get_role_id(emoji_name)

        for role in self.roles:
            if role_id == role.id:
                return role

        return None

    def eligible_for_action(self, payload):
        """
        Determine if a given payload is eligible to be acted on

        Return Bool
        """
        # Update role and emoji ID info
        self.map_role_id()
        self.map_emoji_ids()

        user = self.get_user(payload.user_id)
        # If the user reacting is the bot, return
        if user == self.user:
            return False
        # If the reaction is not on the correct message for manging roles, return.
        # Defined in config/config.json
        if self.get_message_id() != payload.message_id:
            return False
        return True

    def get_role_id(self, react):
        react = emoji.demojize(react)
        with open(self.config_file_location, "r") as config_file:
            config_data = json.load(config_file)
            configured_roles = config_data["roles"]
        for item in configured_roles:
            if item["react"] == react:
                return item["role_id"]


if __name__ in "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    bot = RoleBot(intents=discord.Intents.all())
    bot.run(TOKEN)
