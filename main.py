import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import requests
from datetime import timedelta
from PIL import Image, ImageDraw, ImageFont
import io
import aiohttp
import asyncio

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
APIKEY = os.getenv("API_KEY")
BASE_URL = "https://api.henrikdev.xyz/valorant"
BASE_URL2 = "https://valorant-api.com"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

HEADERS = {
    "Authorization": APIKEY,
    "Accept": "*/*"
}

match_data_list_all = []

async def fetch_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                image_data = io.BytesIO(await response.read())
                return Image.open(image_data)
            else:
                raise Exception(f"Failed to fetch image from {url}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

def combine_images_vertically(image_files):
    # Assuming each image is 1300x150, adjust as needed
    image_width, image_height = 1300, 150
    combined_width = image_width
    combined_height = len(image_files) * image_height

    combined_image = Image.new('RGB', (combined_width, combined_height))

    for index, image_file in enumerate(image_files):
        image = Image.open(image_file.fp)
        y = index * image_height
        combined_image.paste(image, (0, y))

    return combined_image

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
        print(data3)
        response4 = requests.get(f"{BASE_URL}/v4/matches/{regioncode}/{platforms}/{name}/{tag}", headers=HEADERS)
        data4 = response4.json()
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
        
@bot.command()
async def matches(ctx, account_nametag: str):
    class MatchDropdown(discord.ui.Select):
        def __init__(self, match_data_list_all):
            options = []
            for data in match_data_list_all:
                option = discord.SelectOption(label=f"Match {data[0]}", description=f"{data[1]} | {data[2]} | {data[3]} | KDA - {data[4]}/{data[5]}/{data[6]}", value=f"{data[0]},{data[7]}")
                options.append(option)

            super().__init__(placeholder="Select a match", options=options, min_values=1, max_values=1)
            
        async def callback(self, interaction: discord.Interaction):
            selected_value = self.values[0]
            match_number, match_id = selected_value.split(',')
            processing_message2 = await interaction.channel.send(f"Processing Match {match_number} with id {match_id}...")

            await interaction.response.send_message(f"You chose Match {match_number} with id {match_id}")

            await processing_message2.delete()

    class MatchView(discord.ui.View):
        def __init__(self, match_data_list_all):
            super().__init__()
            self.add_item(MatchDropdown(match_data_list_all))
            
    name, tag = account_nametag.split('#')
    resp_account = requests.get(f"{BASE_URL}/v2/account/{name}/{tag}", headers=HEADERS)
    numberof_matches_wanted = 10
    match_number = 1
    processing_message = await ctx.send("Processing Match List...")
    if resp_account.status_code == 200:
        data_account = resp_account.json()
        player_uuid = data_account['data']['puuid']
        nametag = data_account['data']['name'] + "#" + data_account['data']['tag']
        regioncode = data_account['data']['region']
        platforms = data_account['data']['platforms'][0]
        resp_matchlist = requests.get(f"{BASE_URL}/v4/matches/{regioncode}/{platforms}/{name}/{tag}?mode=competitive&size={numberof_matches_wanted}", headers=HEADERS)
        data_matchlist = resp_matchlist.json()
        match_images = []
        for match in data_matchlist['data']:
            match_data_list = []
            
            match_metadata = match['metadata']
            match_id = match_metadata['match_id']
            map_name = match_metadata['map']['name']
            queue_type = match_metadata['queue']['name']
            
            for player in match['players']:
                if player["puuid"] == player_uuid:
                    player_rank_id = player['tier']['id']
                    player_team_id = player['team_id']
                    player_agents_id = player['agent']['id']
                    player_kills = player['stats']['kills']
                    player_deaths = player['stats']['deaths']
                    player_assists = player['stats']['assists']
                    player_killdeath = (player_kills/player_deaths)
                    
                    player_headshots = player['stats']['headshots']
                    player_totalshots = player['stats']['headshots'] + player['stats']['bodyshots'] + player['stats']['legshots']
                    player_headshots_percentage_raw = int((player_headshots / player_totalshots) * 100)
                    player_headshots_percentage_display = f"{player_headshots_percentage_raw}%"
            
            for score in match['teams']:
                if score['team_id'] == player_team_id:
                    player_team_score = score['rounds']['won']
                    enemy_team_score = score['rounds']['lost']
                    match_total_score = f"{player_team_score} : {enemy_team_score}"
                
                
            resp_rank = requests.get(f"{BASE_URL2}/v1/competitivetiers", headers=HEADERS)
            data_rank = resp_rank.json()
            for episode in data_rank['data']:
                if episode["assetObjectName"] == "Episode5_CompetitiveTierDataTable":
                    for rank in episode['tiers']:
                        if rank['tier'] == player_rank_id:
                            player_rank_name = rank['tierName']
                            player_rank_image = rank['largeIcon']
                            player_rank_image_small = rank['smallIcon']
                            
            resp_agent = requests.get(f"{BASE_URL2}/v1/agents/{player_agents_id}", headers=HEADERS)
            data_agent = resp_agent.json()
            player_agent_name = data_agent['data']['displayName']
            player_agent_image = data_agent['data']['displayIcon']
            player_agent_image_small = data_agent['data']['displayIconSmall']
            # Load images
            bg = Image.new("RGB", (1300, 150), (18, 20, 30))
            agent_image_output = await fetch_image(player_agent_image)
            rank_image_output = await fetch_image(player_rank_image)
            agent_image_output = agent_image_output.resize((100, 100))
            rank_image_output = rank_image_output.resize((80, 80))

            # Paste agent
            bg.paste(agent_image_output, (20, 25))

            draw = ImageDraw.Draw(bg)
            font_bold = ImageFont.truetype("fonts/Arial Bold.ttf", 28)
            font_small = ImageFont.truetype("fonts/Arial.ttf", 20)

            # Mode and Map Name
            draw.text((140, 30), f"{queue_type}", font=font_small, fill=(180, 180, 180))
            draw.text((140, 60), f"{map_name}", font=font_bold, fill=(255, 255, 255))
            
            # Match Numbering for Selecting Match Details
            draw.text((140, 90), f"Match {match_number}", font=font_small, fill=(255, 255, 255))
            

            # Rank
            bg.paste(rank_image_output, (450, 30), rank_image_output.convert("RGBA"))
            
            # Match Score
            if player_team_score > enemy_team_score:
                draw.text((560, 60), f"{match_total_score}", font=font_bold, fill=(100, 255, 100))
            elif player_team_score < enemy_team_score:
                draw.text((560, 60), f"{match_total_score}", font=font_bold, fill=(255, 13, 13))
            elif player_team_score == enemy_team_score:
                draw.text((560, 60), f"{match_total_score}", font=font_bold, fill=(128, 128, 128))

            # KDA
            draw.text((800, 30), "K / D / A", font=font_small, fill=(180, 180, 180))
            draw.text((800, 55), f"{player_kills} / {player_deaths} / {player_assists}", font=font_bold, fill=(255, 255, 255))
            if player_killdeath >= 1:
                draw.text((1050, 60), f"{player_killdeath:.1f}", font=font_bold, fill=(100, 255, 100))
            elif player_killdeath < 1:
                draw.text((1050, 60), f"{player_killdeath:.1f}", font=font_bold, fill=(255, 13, 13))
                
            # HS Rate
            draw.text((1200, 60), f"{player_headshots_percentage_display}", font=font_bold, fill=(128, 128, 128)) 
            
            match_data_list.append(match_number)
            match_data_list.append(player_agent_name)
            match_data_list.append(map_name)
            match_data_list.append(match_total_score)
            match_data_list.append(player_kills)
            match_data_list.append(player_deaths)
            match_data_list.append(player_assists)
            match_data_list.append(match_id)
            match_data_list_all.append(match_data_list)
            
            match_number += 1

            image_binary = io.BytesIO()
            bg.save(image_binary, 'PNG')
            image_binary.seek(0)
            match_images.append(discord.File(fp=image_binary, filename=f"matchdetails_{nametag}.png"))
        
        # Send the combined images into batches
        batch_size = 5
        num_batches = 2

        for i in range(num_batches):
            start_index = i * batch_size
            end_index = start_index + batch_size
            images_batch = match_images[start_index:end_index]
            
            print(f"Batch {i+1}: {len(images_batch)} images")

            combined_image = combine_images_vertically(images_batch)
            

            combined_image_binary = io.BytesIO()
            combined_image.save(combined_image_binary, 'PNG')
            combined_image_binary.seek(0)

            await ctx.send(file=discord.File(fp=combined_image_binary, filename=f"combined_matchdetails_{nametag}_{i+1}.png"))
        await processing_message.delete()
        
        await ctx.send("Select a match to view!", view=MatchView(match_data_list_all))
        
        try:
            interaction = await bot.wait_for(
                "interaction", 
                check=lambda i: i.user == ctx.author and i.data['component_type'] == 3,
                timeout=60.0
            )
            selected_value = interaction.data['values'][0]
            match_number, match_id = selected_value.split(',')

            
        except asyncio.TimeoutError:
            await ctx.send("You didn't select a match in time.")

    else:
        await ctx.send("Couldn't fetch the data at the moment.")

bot.run(TOKEN)
