import discord
from discord import app_commands
from discord.ui import Modal, TextInput, View, Button
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

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.channel
        # Webhookを取得または作成
        webhooks = await channel.webhooks()
        webhook = next((w for w in webhooks if w.name == "AnonymousBot"), None)
        if webhook is None:
            webhook = await channel.create_webhook(name="AnonymousBot")

        await webhook.send(
            content=self.message.value,
            username="匿名",
            avatar_url="https://cdn.discordapp.com/embed/avatars/0.png",
        )
        await interaction.response.send_message(
            "✅ 匿名で送信しました！", ephemeral=True
        )


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
        channel_id = config.get(str(interaction.guild_id))
        if channel_id is None or str(interaction.channel_id) != channel_id:
            await interaction.response.send_message(
                "❌ このボタンは匿名投稿チャンネルでのみ使用できます。", ephemeral=True
            )
            return
        await interaction.response.send_modal(AnonModal())


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
    config = load_config()
    config[str(interaction.guild_id)] = str(interaction.channel_id)
    save_config(config)

    await interaction.response.send_message(
        f"✅ <#{interaction.channel_id}> に匿名投稿ボタンを設置しました！",
        ephemeral=True,
    )
    await interaction.channel.send(
        "このチャンネルで匿名メッセージを送ることができます。",
        view=AnonButtonView(),
    )


@setup.error
async def setup_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ このコマンドは管理者のみ使用できます。", ephemeral=True
        )


client.run(TOKEN)
