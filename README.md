# IsekaiBot
Python body of a Discord bot setting up RPG like fantasy game.

The whole bot runs from *IsekaiBot.py*. *encounters.py* was more of a testing ground file for development of the rpg world and *itemizer.py* is a small console script that allows user-input creation of the game Items and Equipment.

**Note:** This repository lacks a .env file that contains the discord application token the bot is associated with (I can't reveal that information as a Discord developer). Thus for the project to be fully working, you will need to provide your own discord bot with its token. Follow these steps:
- pip install both discord and python-dotenv;
- go to https://discord.com/developers/applications.
- follow the instructions on how to get a token at: https://www.writebots.com/discord-bot-token/
- once you have your token, create a *.env* file (no name needed just the extension) in the same folder where the *IsekaiBot.py* file is located.
- open the *.env* and type: **DISCORD_TOKEN =** and paste your token after the equal sign.

With all those done, you will now be ready to run the bot from a terminal.
It is preferable to run it with console printing synchronized to help with debug:

**python -u IsekaiBot.py**

This code is totally open source so feel free to modify the cloned repository as much as you want. :)
dnglokpor
