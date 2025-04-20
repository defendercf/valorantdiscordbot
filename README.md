# 🎮 Valorant Discord Bot

Welcome to the **Simple Valorant Discord Bot!**  
This bot allows you to get quick access to Valorant account details and the current store bundle directly from your Discord server.

## 🚀 Getting Started

1. Make sure to install the required library : 
```bash
pip install discord
```
```bash
pip install requests
```
```bash
pip install dotenv
```
2. Make sure to add these lines to .env file :
```env
DISCORD_TOKEN=YOUR_DISCORDBOT_TOKEN
API_KEY=YOUR_API_KEY
```
3. Make sure to invite the bot to your server and give it the required permissions to read and send messages in your desired channels.
4. Run the main.py on your terminal.
5. Run the command on the discord server.

### 🛠 Commands Overview

| Command | Description |
|---------|-------------|
| `!store` | Displays the current Valorant bundle in the store along with its price. |
| `!account <RiotID#Tag>` | Displays data regarding the specified Valorant account. Example: `!account namtaka#fAz` |
| `!matches <RiotID#Tag>` | Displays the match history with agents, map, stats, kd, and hs percentage. Example:  `!matches namtaka#fAz` |

Made by a fellow Valorant Player
