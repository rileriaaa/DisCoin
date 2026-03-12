import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
from api import get_crypto_price
from database import (init_db, add_to_watchlist, remove_from_watchlist, get_watchlist,
                      create_alert, get_user_alerts, get_all_alerts, delete_alert)
from stocks import get_stock_price

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help') 

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
        alert_id, user_id, coin_name, target_price, condition, asset_type = alert
        
        if asset_type == 'crypto':
            price, _ = get_crypto_price(coin_name)
        else: 
            price, _, _ = get_stock_price(coin_name)
        
        print(f"Checking {coin_name} ({asset_type}): price={price}, target={target_price}, condition={condition}")
        
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
            await user.send(f"{emoji} **ALERT TRIGGERED!**\n{coin_name.upper()} ({asset_type}) is now ${price:,.2f} (target: ${target_price:,.2f} {condition})")
            delete_alert(alert_id)

@check_alerts.before_loop
async def before_check_alerts():
    await bot.wait_until_ready()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(
            title="Command Not Found",
            description="Use `!help` to see available commands.",
            color=0xe74c3c
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="Missing Argument",
            description=f"Usage: `!{ctx.command.name} <argument>`\nUse `!help` for examples.",
            color=0xe74c3c
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(
            title="Invalid Argument",
            description="Check your command syntax with `!help`",
            color=0xe74c3c
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="Error",
            description=f"An error occurred: {str(error)}",
            color=0xe74c3c
        )
        await ctx.send(embed=embed)
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
        price_val, change = get_crypto_price(coin)
        
        if price_val:
            color = 0x00ff00 if change > 0 else 0xff0000 
            embed = discord.Embed(
                title=f"{coin.upper()}",
                color=color,
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Price", value=f"${price_val:,.2f}", inline=True)
            embed.add_field(name="24h Change", value=f"{change:+.2f}%", inline=True)
            embed.set_footer(text="Data from CoinGecko")
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Couldn't find price for '{coin}'. Try: bitcoin, ethereum, solana")


@bot.command()
async def watch(ctx, action: str, asset: str = None, asset_type: str = 'crypto'):
    """Manage watchlist. Usage: !watch add bitcoin crypto OR !watch add AAPL stock"""
    user_id = ctx.author.id
    
    if action == "add":
        if not asset:
            await ctx.send("Please specify an asset to add!")
            return
        
        if add_to_watchlist(user_id, asset, asset_type):
            embed = discord.embeds(
                title='Added to watchlist',
                description=f'**{asset.upper()}** ({asset_type})',
                color=0x2ecc71
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"**{asset.upper()}** is already in your watchlist!")
    
    elif action == "remove":
        if not asset:
            await ctx.send("Please specify an asset to remove!")
            return
        
        if remove_from_watchlist(user_id, asset):
            await ctx.send(f"Removed **{asset.upper()}** from your watchlist!")
        else:
            await ctx.send(f"**{asset.upper()}** is not in your watchlist!")
    
    elif action == "list":
        items = get_watchlist(user_id)
        if items:
            watchlist_text = "**Your watchlist:**\n"
            for name, atype in items:
                watchlist_text += f"• {name.upper()} ({atype})\n"
            await ctx.send(watchlist_text)
        else:
            await ctx.send("Your watchlist is empty! Use `!watch add <asset> <crypto/stock>` to add.")
    
    else:
        await ctx.send("Invalid action! Use: `!watch add/remove/list`")

@bot.command()
async def watchlist(ctx):
    """Show prices for all assets in your watchlist"""
    user_id = ctx.author.id
    items = get_watchlist(user_id)
    
    if not items:
        await ctx.send("📋 Your watchlist is empty!")
        return
    
    embed = discord.Embed(
        title="📊 Your Watchlist",
        color=0x3498db,
        timestamp=discord.utils.utcnow()
    )
    
    for name, asset_type in items:
        if asset_type == 'crypto':
            price_val, change = get_crypto_price(name)
            if price_val:
                emoji = "📈" if change > 0 else "📉"
                embed.add_field(
                    name=f"{emoji} {name.upper()} (Crypto)",
                    value=f"${price_val:,.2f} ({change:+.2f}% 24h)",
                    inline=False
                )
        else:  
            price_val, change, market_state = get_stock_price(name)
            if price_val:
                emoji = "📈" if change > 0 else "📉"
                market_emoji = "🟢" if market_state != "CLOSED" else "🔴"
                embed.add_field(
                    name=f"{emoji} {name.upper()} (Stock) {market_emoji}",
                    value=f"${price_val:,.2f} ({change:+.2f}% today)",
                    inline=False
                )
    
    await ctx.send(embed=embed)

@bot.command()
async def alert(ctx, asset: str, target_price: float, condition: str, asset_type: str = 'crypto'):
    """Set a price alert. Usage: !alert bitcoin 50000 above crypto OR !alert AAPL 150 below stock"""
    if condition.lower() not in ['above', 'below']:
        await ctx.send("Condition must be 'above' or 'below'!")
        return
    
    alert_id = create_alert(ctx.author.id, asset, target_price, condition, asset_type)
    await ctx.send(f"Alert created! I'll notify you when {asset.upper()} ({asset_type}) goes {condition} ${target_price:,.2f} (Alert ID: {alert_id})")

@bot.command()
async def alerts(ctx):
    user_alerts = get_user_alerts(ctx.author.id)
    
    if not user_alerts:
        await ctx.send("You have no active alerts!")
        return
    
    embed = discord.Embed(
        title="Your Active Alerts",
        color=0xe74c3c,
        timestamp=discord.utils.utcnow()
    )
    
    for alert in user_alerts:
        alert_id, coin, price, condition, asset_type = alert
        embed.add_field(
            name=f"Alert #{alert_id}",
            value=f"{coin.upper()} ({asset_type}) {condition} ${price:,.2f}",
            inline=False
        )
    
    embed.set_footer(text="Use !removealert <id> to remove an alert")
    await ctx.send(embed=embed)

@bot.command()
async def removealert(ctx, alert_id: int):
    """Remove an alert by ID. Usage: !removealert 1"""  
    if delete_alert(alert_id):
        await ctx.send(f"Alert {alert_id} removed!")
    else:
        await ctx.send(f"Alert {alert_id} not found!")
        
@bot.command()
async def stock(ctx, *tickers: str):
    """Get stock prices. Usage: !stock AAPL TSLA GOOGL"""
    if not tickers:
        await ctx.send("specify at least one stock ticker.")
        return
    
    for ticker in tickers:
        price, change, market_state = get_stock_price(ticker)
        
        if price:
            color = 0x00ff00 if change > 0 else 0xff0000
            market_emoji = "🟢" if market_state != "CLOSED" else "🔴"
            
            embed = discord.Embed(
                title=f"📊 {ticker.upper()}",
                color=color,
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Price", value=f"${price:,.2f}", inline=True)
            embed.add_field(name="Today's Change", value=f"{change:+.2f}%", inline=True)
            embed.add_field(name="Market Status", value=f"{market_emoji} {market_state}", inline=False)
            embed.set_footer(text="Data from Yahoo Finance")
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"couldn't find stock '{ticker.upper()}'. try: AAPL, TSLA, GOOGL, MSFT")

@bot.command()
async def help(ctx):
    """Show all available commands"""
    embed = discord.Embed(
        title="🤖 TickerBot Commands",
        description="Track crypto and stock prices with alerts and watchlists",
        color=0x3498db
    )
    
    embed.add_field(
        name="📊 Price Commands",
        value=(
            "`!price <coin>` - Get crypto price (e.g., !price bitcoin)\n"
            "`!stock <ticker>` - Get stock price (e.g., !stock AAPL)\n"
            "`!price btc eth sol` - Get multiple prices"
        ),
        inline=False
    )
    
    embed.add_field(
        name="👀 Watchlist",
        value=(
            "`!watch add <asset> <crypto/stock>` - Add to watchlist\n"
            "`!watch remove <asset>` - Remove from watchlist\n"
            "`!watch list` - Show your watchlist\n"
            "`!watchlist` - Show prices of watched assets"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🔔 Alerts",
        value=(
            "`!alert <asset> <price> <above/below> <crypto/stock>`\n"
            "`!alerts` - List your active alerts\n"
            "`!removealert <id>` - Remove an alert"
        ),
        inline=False
    )
    
    embed.add_field(
        name="💡 Examples",
        value=(
            "`!watch add bitcoin crypto`\n"
            "`!alert AAPL 150 below stock`\n"
            "`!price btc eth`"
        ),
        inline=False
    )
    
    embed.set_footer(text="Made by rileriaaa.me | Data from CoinGecko & Yahoo Finance")
    
    await ctx.send(embed=embed)

bot.run(os.getenv('TOKEN'))
            