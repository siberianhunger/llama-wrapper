import os

import telegram.constants
from groq import AsyncGroq
from groq.types.chat import ChatCompletionMessage
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from models import Roles
from logger import logger
from redis_client import get_cached_messages, set_messages_in_cache
import re

groq_client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

model: str = os.environ.get("MODEL") or "llama3-70b-8192"


def prompt_msg_builder(role: Roles, content: str):
    return {"role": role, "content": content}


default_system_prompts = (
    prompt_msg_builder(Roles.system,
                       "If your answer doesn't have any code or some config files don't use MarkdownV2."),
    prompt_msg_builder(Roles.system, "Don't use chinese characters, only Russian and English is allowed."),
    prompt_msg_builder(Roles.system, 'Ответь на русском.'),
)

eng_system_prompts = (
    prompt_msg_builder(Roles.system,
                       "If your answer doesn't have any code or some config files don't use MarkdownV2."),
    prompt_msg_builder(Roles.system, "Don't use chinese or Russian characters, only English is allowed."),
)


async def llama_with_context(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cache_key = f"{update.message.chat_id}_{update.message.from_user.name}_cache"
    parsed_question = update.message.text.replace('/llama', '')
    logger.info(f'new question!: {parsed_question}')
    cached_msgs = await get_cached_messages(cache_key)
    if cached_msgs:
        logger.info(f'conversation with cache!')
        msg_list = [*cached_msgs, prompt_msg_builder(Roles.user, parsed_question)]
        logger.info(f'full msg list: {msg_list}')
        generated_msg = await query_groq_for_data(msg_list)
        await set_messages_in_cache(cache_key, [*msg_list, prompt_msg_builder(Roles.assistant, generated_msg)])
    else:
        logger.info(f'no cache for conversation found!')
        generated_msg = await query_groq_for_data([prompt_msg_builder(Roles.user, parsed_question)])
        await set_messages_in_cache(cache_key, [prompt_msg_builder(Roles.assistant, generated_msg)])
    msg_to_send = f"{update.message.from_user.name}\n{generated_msg}"
    await update.effective_message.reply_text(msg_to_send)


async def lleng(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cache_key = f"{update.message.chat_id}_{update.message.from_user.name}_eng_cache"
    parsed_question = update.message.text.replace('/llama', '')
    logger.info(f'new question!: {parsed_question}')
    cached_msgs = await get_cached_messages(cache_key)
    if cached_msgs:
        logger.info(f'conversation with cache!')
        msg_list = [*cached_msgs, prompt_msg_builder(Roles.user, parsed_question)]
        logger.info(f'full msg list: {msg_list}')
        generated_msg = await query_groq_for_data(msg_list, eng_system_prompts)
        await set_messages_in_cache(cache_key, [*msg_list, prompt_msg_builder(Roles.assistant, generated_msg)])
    else:
        logger.info(f'no cache for conversation found!')
        generated_msg = await query_groq_for_data([prompt_msg_builder(Roles.user, parsed_question)], eng_system_prompts)
        await set_messages_in_cache(cache_key, [prompt_msg_builder(Roles.assistant, generated_msg)])
    msg_to_send = f"{update.message.from_user.name}\n{generated_msg}"
    await update.effective_message.reply_text(msg_to_send)


async def llama_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    parsed_question = update.message.text.replace('/llask', '')
    logger.info(f'llama_ask: {parsed_question}')
    generated_msg = await query_groq_for_data([prompt_msg_builder(Roles.user, parsed_question)])
    msg_to_send = f"{update.message.from_user.name}\n{generated_msg}"
    await update.effective_message.reply_text(msg_to_send)


async def think(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    parsed_question = update.message.text.replace('/llask', '')
    logger.info(f'llama_ask: {parsed_question}')
    generated_msg = await query_groq_for_data([prompt_msg_builder(Roles.user, parsed_question)], think=True)
    msg_to_send = f"{update.message.from_user.name}\n{generated_msg}"
    await update.effective_message.reply_text(msg_to_send)


def remove_think_tags(text):
    # This pattern matches <think> followed by any characters (non-greedily)
    # until the next </think>, taking into account multiple lines.
    pattern = re.compile(r'<think>.*?</think>', re.DOTALL)

    # Use sub() to replace all occurrences of the pattern with an empty string.
    return pattern.sub('', text)


async def query_groq_for_data(
        user_prompts: list[dict],
        sys_promts=default_system_prompts,
        think: bool = False
) -> ChatCompletionMessage:
    chat_completion = await groq_client.chat.completions.create(
        messages=[*sys_promts, *user_prompts],
        model=model,
    )
    response_text = chat_completion.choices[0].message.content
    if think:
        return response_text
    return remove_think_tags(response_text).strip()


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(os.environ.get("TG_BOT_TOKEN")).build()
    application.add_handler(CommandHandler("llama", llama_with_context))
    application.add_handler(CommandHandler("llask", llama_ask))
    application.add_handler(CommandHandler("lleng", lleng))
    application.add_handler(CommandHandler("think", think))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
