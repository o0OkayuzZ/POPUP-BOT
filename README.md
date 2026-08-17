# POPUP-BOT 匿名投稿Discord BOT

特定のチャンネルで `/anon` コマンドを使うと、モーダル（ポップアップ）から匿名でメッセージを投稿できるDiscord BOTです。

## セットアップ手順

### 1. リポジトリをクローン
```bash
git clone https://github.com/o0OkayuzZ/POPUP-BOT.git
cd POPUP-BOT
```

### 2. ライブラリをインストール
```bash
pip install -r requirements.txt
```

### 3. トークンを設定
`.env.example` をコピーして `.env` を作成し、トークンを入力する。
```bash
cp .env.example .env
```
`.env` を開いて編集：
```
DISCORD_TOKEN=あなたのBOTトークンをここに入力
```

### 4. BOTを起動
```bash
python bot.py
```

### 5. 匿名チャンネルを設定
匿名投稿させたいチャンネルで管理者が以下を実行：
```
/setup
```

### 6. 匿名投稿
設定したチャンネルで：
```
/anon
```
ポップアップが表示されるので、メッセージを入力して送信！

## コマンド一覧

| コマンド | 説明 | 権限 |
|---------|------|------|
| `/setup` | 実行したチャンネルを匿名投稿チャンネルに設定 | 管理者のみ |
| `/anon` | 匿名投稿用モーダルを表示 | 全員 |

## 注意事項
- `.env` と `config.json` は `.gitignore` に含まれているためGitHubにはアップロードされません
- BOTトークンは絶対に他人に見せないでください
- サーバーの管理者はDiscordの監査ログからWebhookの投稿を確認できます（完全な匿名ではありません）
