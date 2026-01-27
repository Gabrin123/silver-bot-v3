# Silver Chart Telegram Bot - Complete Setup

## Files Needed:
1. `silver_chart_bot.py` - Main bot script
2. `requirements.txt` - Python dependencies
3. `Dockerfile` - Docker configuration
4. This README

## Deployment Steps:

### 1. Create GitHub Repository
- Go to github.com and create a new repo
- Upload all 3 files (silver_chart_bot.py, requirements.txt, Dockerfile)

### 2. Deploy on Render.com
1. Go to render.com and sign up (free)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: silver-bot (or any name)
   - **Environment**: Docker
   - **Instance Type**: Free

5. Add Environment Variables:
   - Click "Advanced" → "Add Environment Variable"
   - Variable 1:
     - Key: `BOT_TOKEN`
     - Value: `8355694996:AAE5aAFeeA1kFYiQIIe0coD_JdQQ3d6jROA`
   - Variable 2:
     - Key: `CHAT_ID`
     - Value: `375372594`

6. Click "Create Web Service"
7. Wait 2-3 minutes for deployment

## How It Works:
- Bot sends silver price updates to your Telegram every 3 minutes
- Includes link to live TradingView chart
- Runs 24/7 on free hosting

## Customization:
To change update frequency, edit line 168 in `silver_chart_bot.py`:
```python
schedule.every(3).minutes.do(job)
```
Change `3` to any number of minutes you want.

## Your Bot Details:
- Bot Username: @Bigdoggie_bot
- Chat ID: 375372594
- Updates: Every 3 minutes
