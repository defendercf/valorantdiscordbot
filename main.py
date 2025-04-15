import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import requests
from datetime import timedelta

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
APIKEY = os.getenv("API_KEY")
BASE_URL = "https://api.henrikdev.xyz/valorant"
BASE_URL2 = "https://valorant-api.com"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

HEADERS = {
    "Authorization": APIKEY,
    "Accept": "*/*"
}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def store(ctx):
    response = requests.get(f"{BASE_URL}/v2/store-featured", headers=HEADERS)
    
    if response.status_code == 200:
        data = response.json()
        uuid = data['data'][0]['bundle_uuid']
        bundle_price = data['data'][0]['bundle_price']
        bundle_time_seconds = data['data'][0]['seconds_remaining']
        bundle_time = str(timedelta(seconds=bundle_time_seconds))
        response2 = requests.get(f"{BASE_URL2}/v1/bundles/{uuid}", headers=HEADERS)
        data2 = response2.json()
        bundle_name = (data2['data']['displayName']) + " Bundle"
        bundle_image = (data2['data']['displayIcon'])
        embed = discord.Embed(
          title=bundle_name,
          description="The price of the bundle is " + str(bundle_price) + " VP\nRemaining Duration of bundle is " + bundle_time,
          color=discord.Color.blue()
          )
        embed.set_image(url=bundle_image)
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("Couldn't fetch the data at the moment.")
       
@bot.command() 
async def account(ctx, account_nametag: str):
    name, tag = account_nametag.split('#')
    response = requests.get(f"{BASE_URL}/v2/account/{name}/{tag}", headers=HEADERS)
    
    if response.status_code == 200:
        data = response.json()
        nametag = data['data']['name'] + "#" + data['data']['tag']
        acc_level = data['data']['account_level']
        regioncode = data['data']['region']
        if regioncode == "ap":
            region = "Asia Pacific"
        elif regioncode == "na":
            region = "North America"
        elif regioncode == "eu":
            region = "Europe"
        elif regioncode == "kr":
            region = "Korea"
        platforms = data['data']['platforms'][0]
        card_uuid = data['data']['card']
        response2 = requests.get(f"{BASE_URL2}/v1/playercards/{card_uuid}", headers=HEADERS)
        data2 = response2.json()
        card_image = data2['data']['largeArt']
        response3 = requests.get(f"{BASE_URL}/v3/mmr/{regioncode}/{platforms}/{name}/{tag}", headers=HEADERS)
        data3 = response3.json()
        response4 = requests.get(f"{BASE_URL}/v4/matches/{regioncode}/{platforms}/{name}/{tag}", headers=HEADERS)
        data4 = response4.json()
        print(data4)
        peak_rank = data3['data']['peak']['tier']['name']
        current_rank = data3['data']['current']['tier']['name']
        embed = discord.Embed(
          title=nametag,
          description=f"Account level is {acc_level}\nRegion is {region}\nPlays in {platforms}\nCurrent Rank is {current_rank}\nPeak Rank is {peak_rank}",
          color=discord.Color.green()
          )
        embed.set_image(url=card_image)
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("Couldn't fetch the data at the moment.")

bot.run(TOKEN)
