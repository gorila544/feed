import discord
import requests
import asyncio

# 設定
RIOT_API_KEY = ""
DISCORD_BOT_TOKEN = ""
GAME_NAME = ""
TAG_LINE = ""
REGION = ""  # Riot APIではリージョン形式が異なる場合があります
DISCORD_CHANNEL_ID = ""  # 通知を送るDiscordチャンネルID
FEED_THRESHOLD = 10  # 死亡数の閾値

# Riot APIのエンドポイント
BASE_URL = f"https://{REGION}.api.riotgames.com/lol"

# 必要なIntentを設定
intents = discord.Intents.default()
intents.messages = True  # メッセージ関連のIntentを有効化
intents.message_content = True  # メッセージ内容のIntentを有効化

# Botクライアントを作成
client = discord.Client(intents=intents)

# 最後に通知した試合IDを記録
last_notified_match_id = ""

async def check_match_status():
    global last_notified_match_id

    try:
        # サモナー情報を取得
        summoner_url = f"https://{REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{GAME_NAME}/{TAG_LINE}"
        response = requests.get(summoner_url, headers={"X-Riot-Token": RIOT_API_KEY})
        response.raise_for_status()
        summoner_data = response.json()
        encrypted_puuid = summoner_data["puuid"]
        print(encrypted_puuid)

        # 最近の試合IDを取得
        match_list_url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{encrypted_puuid}/ids?start=0&count=1"
        response = requests.get(match_list_url, headers={"X-Riot-Token": RIOT_API_KEY})
        response.raise_for_status()
        recent_match_id = response.json()[0]
        print(f"last_notified_match_id: {last_notified_match_id}")
        print(f"recent_match_id: {recent_match_id}")

        # 試合終了後にまだ通知していない試合を確認
        if recent_match_id != last_notified_match_id:
            # 試合詳細を取得
            match_detail_url = f"https://{REGION}.api.riotgames.com/lol/match/v5/matches/{recent_match_id}"
            response = requests.get(match_detail_url, headers={"X-Riot-Token": RIOT_API_KEY})
            response.raise_for_status()
            match_data = response.json()

            # プレイヤーのデス数をチェック
            for participant in match_data["info"]["participants"]:
                if participant["summonerName"] == GAME_NAME:
                    deaths = participant["deaths"]
                    if deaths >= FEED_THRESHOLD:
                        channel = client.get_channel(DISCORD_CHANNEL_ID)
                        await channel.send(
                            f"⚠️ {GAME_NAME}さんがフィードしました！死亡数: {deaths}"
                        )
                    else:
                        print(f"{GAME_NAME}の死亡数: {deaths}（フィードしていません）")
                    break

            # 通知済みの試合IDを記録
            last_notified_match_id = recent_match_id

    except Exception as e:
        print(f"エラーが発生しました: {e}")

@client.event
async def on_ready():
    print(f"ログインしました: {client.user}")
    while True:
        await check_match_status()
        print("--------------------------------------")
        # 1分ごとにチェック
        await asyncio.sleep(60)

# Botを実行
client.run(DISCORD_BOT_TOKEN)
