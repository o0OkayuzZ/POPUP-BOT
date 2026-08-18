# POPUP-BOT

Discordの特定チャンネルで、名前を出さずに会話できる匿名投稿BOTです。
チャンネル内のボタンを押し、表示されたポップアップへ文章を入力するだけで投稿できます。

## 主な機能

- 投稿者の名前とアイコンを全員共通の「匿名」に統一
- 投稿者が切り替わると発言のまとまりを分け、匿名同士の会話を見やすく表示
- 同じ投稿者の連続投稿は、ひとまとまりの発言として表示
- 投稿のたびに匿名投稿ボタンをチャンネルの一番下へ自動移動
- BOTを再起動しても設置済みのボタンを利用可能

## 必要なもの

- Python 3.10以上
- Discord BOTのトークン
- BOTを導入するDiscordサーバーの管理権限

## セットアップ手順

### 1. Discord BOTを作成

1. [Discord Developer Portal](https://discord.com/developers/applications)で「New Application」を選択します。
2. 左側の「Bot」からBOTを追加し、トークンを取得します。
3. 左側の「OAuth2」→「URL Generator」で `bot` と `applications.commands` を選択します。
4. BOT権限で次を選び、生成されたURLからサーバーへ招待します。

- View Channels（チャンネルを見る）
- Send Messages（メッセージを送信）
- Read Message History（メッセージ履歴を読む）
- Manage Webhooks（Webhookを管理）

特権インテントの設定は不要です。

### 2. リポジトリをクローン

```bash
git clone https://github.com/o0OkayuzZ/POPUP-BOT.git
cd POPUP-BOT
```

### 3. ライブラリをインストール

```bash
python -m pip install -r requirements.txt
```

環境によって `python` が使えない場合は、Windowsでは次を使用します。

```powershell
py -m pip install -r requirements.txt
```

### 4. トークンを設定

`.env.example` をコピーして `.env` を作成します。

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS / Linux:

```bash
cp .env.example .env
```

作成した `.env` を開き、取得したBOTトークンを設定します。

```env
DISCORD_TOKEN=ここにBOTトークンを入力
```

### 5. BOTを起動

```bash
python bot.py
```

Windowsで `python` が使えない場合:

```powershell
py bot.py
```

### 6. 匿名チャンネルを設定

匿名投稿に使用するチャンネルで、サーバー管理者が次のコマンドを実行します。

```text
/setup
```

チャンネルに「匿名メッセージを送る」ボタンが設置されます。

## 使い方

1. 「匿名メッセージを送る」ボタンを押します。
2. ポップアップへメッセージを入力します。
3. 送信すると「匿名」としてチャンネルへ投稿され、ボタンが一番下へ移動します。

## コマンド

| コマンド | 説明 | 権限 |
|---------|------|------|
| `/setup` | 実行したチャンネルを匿名投稿チャンネルに設定 | 管理者のみ |

## 匿名表示の仕組み

表示名とアイコンが同じでも会話を区別できるよう、BOTは2つのWebhookを自動作成して投稿者が変わるたびに切り替えます。利用者がWebhookを準備する必要はありません。

匿名になるのは、Discordチャンネルを閲覧する一般利用者に対してです。BOTは投稿処理のため利用者のDiscord IDを受け取り、直前の投稿者を判定するため `config.json` に最後の投稿者IDを保存します。BOTの管理者に対する完全な匿名を保証するものではありません。

## ファイル

- `.env`: BOTトークンを保存します。GitHubにはアップロードされません。
- `config.json`: サーバーごとのチャンネル、ボタン、直前の投稿状態を保存します。GitHubにはアップロードされません。

## 注意事項

- BOTトークンは公開したり、他人へ渡したりしないでください。
- BOTがオフラインの間はボタンを利用できません。
- GitHubのコードを更新した後は、BOTを再起動または再デプロイしてください。
- 匿名投稿チャンネルを変更する場合は、新しいチャンネルで `/setup` を実行してください。
