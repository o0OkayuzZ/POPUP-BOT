import discord
from discord import app_commands
from discord.ui import Modal, TextInput
import json
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CONFIG_FILE = "config.json"


def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


class AnonModal(Modal, title="匿名メッセージを送信"):
    message = TextInput(
        label="メッセージ内容",
        placeholder="ここに入力...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=2000,
    )

    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.target_channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        # Webhookを取得または作成
        webhooks = await self.target_channel.webhooks()
        webhook = next((w for w in webhooks if w.name == "AnonymousBot"), None)
        if webhook is None:
            webhook = await self.target_channel.create_webhook(name="AnonymousBot")

        await webhook.send(
            content=self.message.value,
            username="匿名",
            avatar_url="https://cdn.discordapp.com/embed/avatars/0.png",
        )
        await interaction.response.send_message(
            "✅ 匿名で送信しました！", ephemeral=True
        )


class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


client = MyClient()


@client.event
async def on_ready():
    print(f"BOT起動: {client.user}")


@client.tree.command(name="setup", description="このチャンネルを匿名投稿チャンネルに設定します（管理者専用）")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    config = load_config()
    config[str(interaction.guild_id)] = str(interaction.channel_id)
    save_config(config)
    await interaction.response.send_message(
        f"✅ <#{interaction.channel_id}> を匿名投稿チャンネルに設定しました！",
        ephemeral=True,
    )


@client.tree.command(name="anon", description="匿名でメッセージを投稿します")
async def anon(interaction: discord.Interaction):
    config = load_config()
    channel_id = config.get(str(interaction.guild_id))

    if channel_id is None:
        await interaction.response.send_message(
            "❌ このサーバーでは匿名チャンネルが設定されていません。管理者に `/setup` を実行してもらってください。",
            ephemeral=True,
        )
        return

    if str(interaction.channel_id) != channel_id:
        await interaction.response.send_message(
            f"❌ このコマンドは <#{channel_id}> でのみ使えます。",
            ephemeral=True,
        )
        return

    channel = interaction.channel
    await interaction.response.send_modal(AnonModal(channel))


@setup.error
async def setup_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ このコマンドは管理者のみ使用できます。", ephemeral=True
        )


client.run(TOKEN)
