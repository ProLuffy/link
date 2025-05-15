# plugins/FSub.py
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS
from database.database import add_fsub_channel, remove_fsub_channel, get_fsub_channels

@Client.on_message(filters.command('addfsub') & filters.private & filters.user(ADMINS))
async def add_fsub_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>Please provide a channel ID or username. Usage: /addfsub @channel_username or /addfsub -100123456789</b>",
            parse_mode="HTML"
        )
    
    channel_identifier = message.command[1]
    try:
        # Resolve channel ID from username or use provided ID
        if channel_identifier.startswith('@'):
            chat = await client.get_chat(channel_identifier)
            channel_id = chat.id
        else:
            channel_id = int(channel_identifier)
        
        # Verify bot is admin in the channel
        chat_member = await client.get_chat_member(channel_id, client.me.id)
        if chat_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply_text(
                "<b>I must be an admin in the channel to manage FSub!</b>",
                parse_mode="HTML"
            )
        
        # Add channel to FSub list
        added = await add_fsub_channel(channel_id)
        if added:
            await message.reply_text(
                f"<b>Channel {channel_identifier} added to FSub list!</b>",
                parse_mode="HTML"
            )
        else:
            await message.reply_text(
                f"<b>Channel {channel_identifier} is already in the FSub list or invalid!</b>",
                parse_mode="HTML"
            )
    except Exception as e:
        await message.reply_text(
            f"<b>Error adding FSub channel: {str(e)}</b>",
            parse_mode="HTML"
        )

@Client.on_message(filters.command('removefsub') & filters.private & filters.user(ADMINS))
async def remove_fsub_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "<b>Please provide a channel ID or username. Usage: /removefsub @channel_username or /removefsub -100123456789</b>",
            parse_mode="HTML"
        )
    
    channel_identifier = message.command[1]
    try:
        # Resolve channel ID from username or use provided ID
        if channel_identifier.startswith('@'):
            chat = await client.get_chat(channel_identifier)
            channel_id = chat.id
        else:
            channel_id = int(channel_identifier)
        
        # Remove channel from FSub list
        removed = await remove_fsub_channel(channel_id)
        if removed:
            await message.reply_text(
                f"<b>Channel {channel_identifier} removed from FSub list!</b>",
                parse_mode="HTML"
            )
        else:
            await message.reply_text(
                f"<b>Channel {channel_identifier} is not in the FSub list!</b>",
                parse_mode="HTML"
            )
    except Exception as e:
        await message.reply_text(
            f"<b>Error removing FSub channel: {str(e)}</b>",
            parse_mode="HTML"
        )

@Client.on_message(filters.command('listfsub') & filters.private & filters.user(ADMINS))
async def list_fsub_command(client: Client, message: Message):
    try:
        fsub_channels = await get_fsub_channels()
        if not fsub_channels:
            return await message.reply_text(
                "<b>No FSub channels configured!</b>",
                parse_mode="HTML"
            )
        
        channel_list = []
        for channel_id in fsub_channels:
            try:
                chat = await client.get_chat(channel_id)
                channel_list.append(f"• {chat.title} (@{chat.username or channel_id})")
            except:
                channel_list.append(f"• Channel ID: {channel_id} (Invalid or inaccessible)")
        
        await message.reply_text(
            "<b>FSub Channels:\n\n" + "\n".join(channel_list) + "</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.reply_text(
            f"<b>Error listing FSub channels: {str(e)}</b>",
            parse_mode="HTML"
      )
