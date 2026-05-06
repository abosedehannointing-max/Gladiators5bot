import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
import pytesseract
import requests
from io import BytesIO

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from environment variable
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when /start is issued."""
    welcome_message = (
        "👋 Welcome to Gladiators OCR Bot!\n\n"
        "Send me any image, and I'll extract the text from it.\n\n"
        "Supported formats: JPEG, PNG, WebP\n"
        "Just send an image and get the text instantly!"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a help message when /help is issued."""
    help_text = (
        "📖 How to use:\n"
        "1. Send me any image (photo or document)\n"
        "2. I'll extract the text from it\n"
        "3. You'll receive the extracted text\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/about - About this bot"
    )
    await update.message.reply_text(help_text)

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send about info."""
    about_text = (
        "🤖 Gladiators OCR Bot v1.0\n"
        "Converts images to text using OCR technology\n"
        "Powered by Tesseract OCR"
    )
    await update.message.reply_text(about_text)

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming images and extract text."""
    try:
        # Send processing message
        processing_msg = await update.message.reply_text("🔄 Processing image... Please wait.")
        
        # Get the photo or document
        if update.message.photo:
            # Get the largest photo
            photo_file = await update.message.photo[-1].get_file()
        elif update.message.document and update.message.document.mime_type.startswith('image/'):
            photo_file = await update.message.document.get_file()
        else:
            await processing_msg.edit_text("❌ Please send a valid image file.")
            return
        
        # Download image
        image_response = requests.get(photo_file.file_path)
        image = Image.open(BytesIO(image_response.content))
        
        # Extract text using pytesseract
        extracted_text = pytesseract.image_to_string(image)
        
        # Clean up the text
        extracted_text = extracted_text.strip()
        
        # Send result
        if extracted_text:
            # If text is too long, split into multiple messages
            if len(extracted_text) > 4000:
                for i in range(0, len(extracted_text), 4000):
                    await update.message.reply_text(
                        f"📝 Extracted Text (Part {i//4000 + 1}):\n\n{extracted_text[i:i+4000]}"
                    )
            else:
                await update.message.reply_text(f"📝 Extracted Text:\n\n{extracted_text}")
            
            await processing_msg.delete()
        else:
            await processing_msg.edit_text(
                "❌ No text found in the image.\n\n"
                "Try sending a clearer image with better contrast."
            )
            
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text(
            "❌ An error occurred while processing the image.\n"
            "Please try again with a different image."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "⚠️ An unexpected error occurred. Please try again later."
        )

def main():
    """Start the bot."""
    if not TOKEN:
        logger.error("No TELEGRAM_BOT_TOKEN found in environment variables!")
        return
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(MessageHandler(
        filters.Document.IMAGE, 
        handle_image
    ))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
