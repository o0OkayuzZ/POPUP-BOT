import discord
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button
import json
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CONFIG_FILE = "config.json"
ANON_WEBHOOK_NAMES = ("AnonymousBot-1", "AnonymousBot-2")
BUTTON_MESSAGE = "このチャンネルで匿名メッセージを送ることができます。"
channel_locks: dict[int, asyncio.Lock] = {}


def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_guild_config(config: dict, guild_id: int) -> dict | None:
    guild_config = config.get(str(guild_id))
    if isinstance(guild_config, str):
        guild_config = {"channel_id": guild_config}
        config[str(guild_id)] = guild_config
    return guild_config


async def move_button_to_bottom(channel: discord.TextChannel, guild_config: dict):
    old_message_id = guild_config.get("button_message_id")
    button_message = await channel.send(BUTTON_MESSAGE, view=AnonButtonView())
    guild_config["button_message_id"] = str(button_message.id)

    if old_message_id is not None:
        try:
            old_message = await channel.fetch_message(int(old_message_id))
            await old_message.delete()
        except discord.HTTPException:
            pass


async def get_anon_webhooks(channel: discord.TextChannel):
    webhooks = await channel.webhooks()
    result = []
    for name in ANON_WEBHOOK_NAMES:
        webhook = next((item for item in webhooks if item.name == name), None)
        if webhook is None:
            webhook = await channel.create_webhook(name=name)
        result.append(webhook)
    return result


class AnonModal(Modal, title="匿名メッセージを送信"):
    def __init__(self, button_message_id: int | None = None):
        super().__init__()
        self.button_message_id = button_message_id

    message = TextInput(
        label="メッセージ内容",
        placeholder="ここに入力...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=2000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel) or interaction.guild_id is None:
            await interaction.response.send_message(
                "❌ この場所では匿名投稿できません。", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        lock = channel_locks.setdefault(channel.id, asyncio.Lock())
        async with lock:
            config = load_config()
            guild_config = get_guild_config(config, interaction.guild_id)
            if guild_config is None or str(channel.id) != guild_config.get("channel_id"):
                await interaction.followup.send(
                    "❌ このチャンネルでは匿名投稿できません。", ephemeral=True
                )
                return

            current_button_id = guild_config.get("button_message_id")
            if self.button_message_id is not None and current_button_id in (
                None,
                str(self.button_message_id),
            ):
                guild_config["button_message_id"] = str(self.button_message_id)

            webhook_slot = int(guild_config.get("webhook_slot", 0))
            user_id = str(interaction.user.id)
            if guild_config.get("last_user_id") not in (None, user_id):
                webhook_slot = 1 - webhook_slot

            try:
                webhooks = await get_anon_webhooks(channel)
                await webhooks[webhook_slot].send(
                    content=self.message.value,
                    username="匿名",
                    avatar_url="https://cdn.discordapp.com/embed/avatars/0.png",
                )
            except discord.Forbidden:
                await interaction.followup.send(
                    "❌ 匿名投稿できませんでした。管理者がBOTに「Webhookを管理」の権限を付けてください。",
                    ephemeral=True,
                )
                return
            except discord.HTTPException:
                await interaction.followup.send(
                    "❌ Discordへの投稿に失敗しました。少し待ってからもう一度送信してください。",
                    ephemeral=True,
                )
                return

            guild_config["last_user_id"] = user_id
            guild_config["webhook_slot"] = webhook_slot
            await move_button_to_bottom(channel, guild_config)
            save_config(config)

        await interaction.followup.send("✅ 匿名で送信しました！", ephemeral=True)


class AnonButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📨 匿名メッセージを送る",
        style=discord.ButtonStyle.primary,
        custom_id="anon_button_persistent",
    )
    async def send_anon(self, interaction: discord.Interaction, button: Button):
        config = load_config()
        guild_config = get_guild_config(config, interaction.guild_id)
        channel_id = guild_config.get("channel_id") if guild_config else None
        if channel_id is None or str(interaction.channel_id) != channel_id:
            await interaction.response.send_message(
                "❌ このボタンは匿名投稿チャンネルでのみ使用できます。", ephemeral=True
            )
            return
        button_message_id = interaction.message.id if interaction.message else None
        await interaction.response.send_modal(AnonModal(button_message_id))


class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.add_view(AnonButtonView())
        await self.tree.sync()


client = MyClient()


@client.event
async def on_ready():
    print(f"BOT起動: {client.user}")


@client.tree.command(name="setup", description="このチャンネルに匿名投稿ボタンを設置します（管理者専用）")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    channel = interaction.channel
    if not isinstance(channel, discord.TextChannel) or interaction.guild_id is None:
        await interaction.response.send_message(
            "❌ サーバーのテキストチャンネルで実行してください。", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    bot_member = channel.guild.me
    if bot_member is None or not channel.permissions_for(bot_member).manage_webhooks:
        await interaction.followup.send(
            "❌ BOTに「Webhookを管理」の権限を付けてから、もう一度 `/setup` を実行してください。",
            ephemeral=True,
        )
        return

    config = load_config()
    guild_config = get_guild_config(config, interaction.guild_id) or {}
    guild_config["channel_id"] = str(interaction.channel_id)
    config[str(interaction.guild_id)] = guild_config

    try:
        await move_button_to_bottom(channel, guild_config)
    except discord.Forbidden:
        await interaction.followup.send(
            "❌ ボタンを設置できませんでした。BOTに「チャンネルを見る」と「メッセージを送信」の権限を付けてください。",
            ephemeral=True,
        )
        return
    except discord.HTTPException:
        await interaction.followup.send(
            "❌ Discordへの送信に失敗しました。少し待ってからもう一度 `/setup` を実行してください。",
            ephemeral=True,
        )
        return

    save_config(config)
    await interaction.followup.send(
        f"✅ <#{interaction.channel_id}> に匿名投稿ボタンを設置しました！",
        ephemeral=True,
    )


@setup.error
async def setup_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ このコマンドは管理者のみ使用できます。", ephemeral=True
        )


client.run(TOKEN)
