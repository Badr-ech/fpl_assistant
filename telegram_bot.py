import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
import httpx
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_URL = os.environ.get("FPL_ASSISTANT_API_URL", "http://localhost:8000")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ASK_TEAM_ID, = range(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return ConversationHandler.END
    await update.message.reply_text(
        "Welcome to FPL Assistant Bot!\nSend /analyze to get team analysis, transfer suggestions, and captain pick."
    )

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return ConversationHandler.END
    await update.message.reply_text("Please send your FPL Team ID:")
    return ASK_TEAM_ID

async def handle_team_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        if update.message:
            await update.message.reply_text("No team ID provided. Operation cancelled.")
        return ConversationHandler.END
    
    team_id = update.message.text.strip()
    await update.message.reply_text("Fetching your team and recommendations...")
    
    try:
        async with httpx.AsyncClient() as client:
            # Get team info
            team_resp = await client.get(f"{API_URL}/team/{team_id}")
            team_resp.raise_for_status()
            players = team_resp.json()
            
            # Create Team object with proper structure
            team = {
                "players": players,
                "total_value": sum(p["price"] for p in players),
                "remaining_budget": 100.0  # Default budget, could be fetched from API
            }
            
            # Get transfer suggestions
            transfers_resp = await client.post(
                f"{API_URL}/recommendations/transfers", 
                json=team,
                params={"budget": 100.0, "gameweek": 1, "subscription_tier": "basic"}
            )
            transfers = transfers_resp.json() if transfers_resp.status_code == 200 else []
            
            # Get captain pick
            captain_resp = await client.post(
                f"{API_URL}/captain/best", 
                json=team,
                params={"gameweek": 1, "subscription_tier": "basic"}
            )
            captain = captain_resp.json() if captain_resp.status_code == 200 else None
            
            # Get team score
            score_resp = await client.post(
                f"{API_URL}/team-score/rate", 
                json=team,
                params={"gameweek": 1}
            )
            score = score_resp.json() if score_resp.status_code == 200 else {}
            
        # Format the response message
        msg = f"🏆 **Your FPL Team Analysis**\n\n"
        msg += f"📊 **Team Score:** {score.get('score', 'N/A')}/100\n"
        
        if score.get('suggestions'):
            msg += f"💡 **Suggestions:** {', '.join(score['suggestions'])}\n"
        
        if captain and captain.get('name'):
            msg += f"👑 **Recommended Captain:** {captain['name']}\n"
            if captain.get('reasoning'):
                msg += f"📝 *Reason:* {captain['reasoning']}\n"
        
        if transfers:
            msg += f"\n📈 **Top Transfer Recommendations:**\n"
            for i, transfer in enumerate(transfers[:3], 1):  # Show top 3
                player_out = transfer.get('player_out', {})
                player_in = transfer.get('player_in', {})
                impact = transfer.get('predicted_impact', 0)
                
                if player_out.get('name') and player_in.get('name'):
                    msg += f"{i}. OUT: {player_out['name']} → IN: {player_in['name']}"
                    if impact:
                        msg += f" (Impact: +{impact:.1f}pts)"
                    msg += "\n"
        
        if not transfers:
            msg += "\n📈 **Transfers:** No recommendations available at the moment\n"
        
        if update.message:
            await update.message.reply_text(msg, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"Bot error: {e}")
        if update.message:
            await update.message.reply_text("Sorry, there was an error fetching your recommendations. Please try again later.")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

def main():
    import os
    from telegram.ext import ApplicationBuilder
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN not set in environment.")
        return
    app = ApplicationBuilder().token(token).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("analyze", analyze)],
        states={
            ASK_TEAM_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_team_id)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("cancel", cancel))
    app.run_polling()

if __name__ == "__main__":
    main()
