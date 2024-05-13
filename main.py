import os
from groq import Groq
import logging
from langdetect import detect

from telegram import Update
from telegram.ext import (
    Application,

    CommandHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
groq_client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)
model: str = os.environ.get("MODEL") or "llama3-70b-8192"


async def llama_call(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_to_reply = update.message.from_user.name or ''
    lang = detect(update.message.text)
    localized_question = f"/{lang}\n {update.message.text}"
    generated_msg = await query_groq_for_data(request_sentence=localized_question)
    msg_to_send = f"{user_to_reply}\n{generated_msg}"
    await update.effective_message.reply_text(msg_to_send)


async def query_groq_for_data(request_sentence: str) -> str:
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": request_sentence,
            }
        ],
        model=model,
    )

    return chat_completion.choices[0].message.content


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(os.environ.get("TG_BOT_TOKEN")).build()

    application.add_handler(CommandHandler("llama", llama_call))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
