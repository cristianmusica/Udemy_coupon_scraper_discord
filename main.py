import requests
from bs4 import BeautifulSoup
import sqlite3
import discord
from discord.ext import commands
import asyncio

TOKEN = 'TOKEN_DC_BOT'
CHANNEL_ID = 'CHANNEL_ID_LOGS'

bot = commands.Bot(command_prefix='!')

db = sqlite3.connect('couponscorpion.db')
cur = db.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS coupon(
    url TEXT,
    timestamp INTEGER
)""")
db.commit()

url = 'https://couponscorpion.com/'

async def scrape_coupons_periodically():
    await bot.wait_until_ready()
    while not bot.is_closed():
        coupons = BeautifulSoup(requests.get(url).text, 'lxml')
        couponsurl = [x.a.get('href') for x in coupons.findAll('h3', class_="flowhidden mb10 fontnormal position-relative")]

        for i in couponsurl:
            cur.execute("SELECT count(*) FROM coupon WHERE url = ?", (i,))
            if (cur.fetchall()[0][0]) == 0:
                channel = bot.get_channel(int(CHANNEL_ID))
                await channel.send(i)
                cur.execute("INSERT INTO coupon (url, timestamp) VALUES (?, strftime('%s','now'))", (i,))
                db.commit()

        cur.execute("DELETE FROM coupon WHERE timestamp < strftime('%s','now') - 30*24*60*60")
        db.commit()
        await asyncio.sleep(3600)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f'Pong! Latency is {latency}ms')

@bot.command()
async def sent_coupons_count(ctx):
    cur.execute("SELECT COUNT(*) FROM coupon")
    count = cur.fetchone()[0]
    await ctx.send(f'Total coupons sent: {count}')

@bot.command()
async def latest_coupon(ctx):
    coupons = BeautifulSoup(requests.get(url).text, 'lxml')
    latest_coupon_element = coupons.find('h3', class_="flowhidden mb10 fontnormal position-relative")
    if latest_coupon_element:
        latest_coupon = latest_coupon_element.a['href']
        await ctx.send(f'Latest coupon: {latest_coupon}')
    else:
        await ctx.send("No latest coupon found.")

bot.loop.create_task(scrape_coupons_periodically())

bot.run(TOKEN)
