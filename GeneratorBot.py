import discord
from discord.ext import commands
import random
import json
import os
import asyncio

config_file = 'config.json'

with open(config_file, 'r') as file:
    config = json.load(file)

TOKEN = config['token']
TEXT_FILES_DIRECTORY = 'accounts'
PREMIUM_ROLE_ID = config['premium_role_id']
NON_PREMIUM_COOLDOWN_TIME = 60
PREMIUM_COOLDOWN_TIME = 30
GEN_COMMAND_CHANNEL_ID = config['gen_command_channel_id']

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='.', intents=intents)
bot.premium_cooldowns = commands.CooldownMapping.from_cooldown(1, PREMIUM_COOLDOWN_TIME, commands.BucketType.user)
bot.non_premium_cooldowns = commands.CooldownMapping.from_cooldown(1, NON_PREMIUM_COOLDOWN_TIME, commands.BucketType.user)


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command(name='gen')
async def generate_line(ctx, service: str = None):
    if ctx.channel.id != int(GEN_COMMAND_CHANNEL_ID):
        await ctx.send('This command can only be used in the generator channel. Made by Crys#0001')
        return

    if not service:
        usage = f"Usage: {ctx.prefix}gen <service>"
        await ctx.send(usage)
        return

    premium_role = ctx.guild.get_role(PREMIUM_ROLE_ID)
    if premium_role and premium_role in ctx.author.roles:
        bucket = bot.premium_cooldowns.get_bucket(ctx.message)
    else:
        bucket = bot.non_premium_cooldowns.get_bucket(ctx.message)

    retry_after = bucket.update_rate_limit()
    if retry_after:
        await ctx.send(f'This command is on cooldown. Please try again in {retry_after:.1f} seconds. Made by Crys#0001')
        return

    service_file = os.path.join(TEXT_FILES_DIRECTORY, f'{service.lower()}.txt')

    if not os.path.isfile(service_file):
        await ctx.send(f'The {service} service does not exist.')
        return

    lines = []
    with open(service_file, 'r') as file:
        lines = file.readlines()

    if not lines:
        await ctx.send(f'No lines available for the {service} service. Made by Crys#0001')
        return

    selected_line = random.choice(lines)
    lines.remove(selected_line)

    with open(service_file, 'w') as file:
        file.writelines(lines)

    try:
        response = f"Generated {service.capitalize()}:\n\n**{selected_line.strip()}**\n\nThank you for using our service! Made by Crys#0001"
        await ctx.author.send(response)
        await ctx.send('Sent to DMS.')
    except discord.Forbidden:
        await ctx.send('Unable to send a private message. Please enable DMs from server members.')

@bot.command(name='stock')
async def show_stock(ctx):
    stock_info = []

    files = [f for f in os.listdir(TEXT_FILES_DIRECTORY) if os.path.isfile(os.path.join(TEXT_FILES_DIRECTORY, f)) and f.endswith('.txt')]

    if not files:
        await ctx.send('No text files in stock.')
    else:
        for file in files:
            service_name = os.path.splitext(file)[0]
            file_path = os.path.join(TEXT_FILES_DIRECTORY, file)

            with open(file_path, 'r') as f:
                lines = f.readlines()

            line_count = len(lines)
            stock_info.append(f'{service_name.capitalize()}: {line_count} Accounts')

        stock_message = f'Stock for {ctx.guild.name}\n\n' + '\n'.join(stock_info)
        usage_message = f"Usage: `.gen <service>`\n\nPlease use the above command followed by one of the available services to generate an account. Made by Crys#0001"

        await ctx.send(f"{stock_message}\n\n{usage_message}")

@bot.event
async def on_message(message):
    if bot.user in message.mentions:
        prefix = bot.command_prefix
        usage = f"Usage: {prefix}gen <service>"
        stock_message = f"Please use the `{prefix}stock` command to check the available services."
        await message.channel.send(f"{stock_message}\n\n{usage}")
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send("This command is on cooldown. Please try again later.")

bot.run(TOKEN)
