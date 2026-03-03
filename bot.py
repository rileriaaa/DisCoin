import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
from api import get_crypto_price
from database import (init_db, add_to_watchlist, remove_from_watchlist, get_watchlist,
                      create_alert, get_user_alerts, get_all_alerts, delete_alert)

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    init_db()
    check_alerts.start()
    print(f'{bot.user} is now online!')
    
@tasks.loop(minutes=2)
async def check_alerts():
    print("Checking alerts...") 
    alerts = get_all_alerts()
    print(f"Found {len(alerts)} alerts")
    
    for alert in alerts:
        alert_id, user_id, coin_name, target_price, condition = alert
        
        price, _ = get_crypto_price(coin_name)
        
        if not price:
            continue
        
        triggered = False
        if condition == "above" and price >= target_price:
            triggered = True
        elif condition == "below" and price <= target_price:
            triggered = True
        
        if triggered:
            print(f"Alert {alert_id} triggered!")
            user = await bot.fetch_user(user_id)
            emoji = "🚨"
            await user.send(f"{emoji} **ALERT TRIGGERED!**\n{coin_name.upper()} is now ${price:,.2f} (target: ${target_price:,.2f} {condition})")
            delete_alert(alert_id)

@check_alerts.before_loop
async def before_check_alerts():
    await bot.wait_until_ready()

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


@bot.command()
async def watch(ctx, action: str, coin: str = None):
    """Manage watchlist. Usage: !watch add bitcoin, !watch remove bitcoin, !watch list"""
    user_id = ctx.author.id
    
    if action == "add":
        if not coin:
            await ctx.send("Please specify a coin to add!")
            return
        
        if add_to_watchlist(user_id, coin):
            await ctx.send(f"Added **{coin.upper()}** to your watchlist!")
        else:
            await ctx.send(f"**{coin.upper()}** is already in your watchlist!")
    
    elif action == "remove":
        if not coin:
            await ctx.send("Please specify a coin to remove!")
            return
        
        if remove_from_watchlist(user_id, coin):
            await ctx.send(f"Removed **{coin.upper()}** from your watchlist!")
        else:
            await ctx.send(f"**{coin.upper()}** is not in your watchlist!")
    
    elif action == "list":
        coins = get_watchlist(user_id)
        if coins:
            await ctx.send(f"Your watchlist: {', '.join([c.upper() for c in coins])}")
        else:
            await ctx.send("Your watchlist is empty! Use `!watch add <coin>` to add coins.")
    
    else:
        await ctx.send("Invalid action! Use: `!watch add/remove/list`")

@bot.command()
async def watchlist(ctx):
    user_id = ctx.author.id
    coins = get_watchlist(user_id)
    
    if not coins:
        await ctx.send("Your watchlist is empty! Use `!watch add <coin>` to add coins.")
        return
    
    await ctx.send("**Your Watchlist Prices:**")
    for coin in coins:
        price_val, change = get_crypto_price(coin)
        if price_val:
            emoji = "📈" if change > 0 else "📉"
            await ctx.send(f"{emoji} **{coin.upper()}**: ${price_val:,.2f} ({change:+.2f}% 24h)")
        else:
            await ctx.send(f"Couldn't fetch price for {coin.upper()}")

@bot.command()
async def alert(ctx, coin: str, target_price: float, condition: str):
    if condition.lower() not in ['above', 'below']:
        await ctx.send("Condition must be 'above' or 'below'!, price in USD")
        return
    
    alert_id = create_alert(ctx.author.id, coin, target_price, condition)
    await ctx.send(f"Alert created! I'll notify you when {coin.upper()} goes {condition} ${target_price:,.2f} (Alert ID: {alert_id})")

@bot.command()
async def alerts(ctx):
    """List your active alerts"""
    user_alerts = get_user_alerts(ctx.author.id)
    
    if not user_alerts:
        await ctx.send("You have no active alerts!")
        return
    
    alert_list = "**Your Active Alerts:**\n"
    for alert in user_alerts:
        alert_id, coin, price, condition = alert
        alert_list += f"ID {alert_id}: {coin.upper()} {condition} ${price:,.2f}\n"
    
    await ctx.send(alert_list)

@bot.command()
async def removealert(ctx, alert_id: int):
    """Remove an alert by ID. Usage: !removealert 1"""
    if delete_alert(alert_id):
        await ctx.send(f"Alert {alert_id} removed!")
    else:
        await ctx.send(f"Alert {alert_id} not found!")

bot.run(os.getenv('TOKEN'))
            