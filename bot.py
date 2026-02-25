import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from api import get_crypto_price

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} is now online!')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("command not found! use `!help` to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"missing argument! uusage: `!{ctx.command.name} <coin name>`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("invalid argument provided!")
    else:
        await ctx.send(f"an error occurred: {str(error)}")
        print(f"Error: {error}")

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')
    

@bot.command()
async def price(ctx, *coins: str):
    
    if not coins:
        await ctx.send("specify at least one coin.")
        return
    
    for coin in coins:
        coin = coin.lower()
        price, change = get_crypto_price(coin)
        
        if price:
            emoji = "📈" if change > 0 else "📉"
            await ctx.send(f"{emoji} **{coin.upper()}**: ${price:,.2f} ({change:+.2f}% 24h)")
        else:
            await ctx.send(f"Couldn't find price for '{coin}'. Try: bitcoin, ethereum, solana")

bot.run(os.getenv('TOKEN'))