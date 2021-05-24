import os
import discord
from bot import RoleBot
import json
import asyncio
from threading import Thread
from flask import Flask, request, render_template, redirect

configFileLocation = os.path.join(
    os.path.dirname(__file__), "config/config.json")
TOKEN = os.getenv("DISCORD_TOKEN")
bot = RoleBot(intents=discord.Intents.all())
app = Flask(__name__)


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


app.run()
