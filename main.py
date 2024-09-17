#!/usr/bin/env python3

import sys
import discord
from discord.ext import commands
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

token = ""
try:
    with open('token.txt') as t:
        token = t.read()
except Exception as e:
    print(e)
    print("Missing token.")
    print("Edit 'token.txt' and add your token accordingly.")
    print("Press Enter to continue...")
    input()
    sys.exit(0)

async def start_bot():
    bot = commands.Bot(command_prefix=".ttc", intents=discord.Intents.all(), help_command=None)
    await bot.load_extension('cogs.ttc_cog')
    return bot

async def main():
    bot = await start_bot()
    await bot.start(f'{token}')

if __name__ == '__main__':
    asyncio.run(main())

# if db doesn't exist create it
# make channel id work
# un-hardcode user and channel id
# compile to exe and make sure that works