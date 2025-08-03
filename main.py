import discord
from discord.ext import commands
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

# 1. ตั้งค่า Spotify API Keys ของคุณ
# *** เปลี่ยน 'YOUR_SPOTIFY_CLIENT_ID' และ 'YOUR_SPOTIFY_CLIENT_SECRET' เป็นรหัสจริงของคุณ ***
SPOTIPY_CLIENT_ID = '653aff1d34b94289afeeca276fb0b879'
SPOTIPY_CLIENT_SECRET = '35c8f81113254613bb9640dd55dfe144'

# 2. ตั้งค่า Discord Bot Token ของคุณ
# *** เปลี่ยน 'YOUR_BOT_TOKEN' เป็น Token จริงของคุณ ***
BOT_TOKEN = 'MTQwMTQwMTQ4MTYzODQ0NTA2Ng.GKiyt9.JI7DZjaf4ChcD7Sd1wPd6nRaGnf1XtU7Ay_9-w'

# 3. ตั้งค่า FFmpeg executable
# ตรวจสอบว่าไฟล์ ffmpeg.exe อยู่ในโฟลเดอร์เดียวกันกับโค้ดหรือไม่
if os.path.exists("../ffmpeg.exe"):
    FFMPEG_PATH = "../ffmpeg.exe"
else:
    FFMPEG_PATH = "ffmpeg"  # ใช้ชื่อ ffmpeg เฉยๆ ถ้าตั้งค่า Path ในระบบแล้ว

# 4. ตั้งค่า Spotify API
try:
    client_credentials_manager = SpotifyClientCredentials(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET
    )
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    print("Spotify API connected successfully!")
except Exception as e:
    print(f"Failed to connect to Spotify API: {e}")
    sp = None

# กำหนดสิทธิ์การเข้าถึง (Intents) ของบอท
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# สร้าง Bot instance พร้อมกำหนด prefix สำหรับคำสั่ง
bot = commands.Bot(command_prefix='!', intents=intents)


# Event นี้จะทำงานเมื่อ Bot ออนไลน์และพร้อมใช้งาน
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    print('Bot is ready to go!')


# คำสั่ง !hello: บอทจะตอบกลับคำทักทาย
@bot.command()
async def hello(ctx):
    await ctx.send(f'Hello! I am {bot.user.name}')


# คำสั่ง !join: ให้บอทเข้าสู่ช่องเสียง
@bot.command()
async def join(ctx):
    if not ctx.author.voice:
        await ctx.send("คุณต้องอยู่ในช่องเสียงก่อนถึงจะใช้คำสั่งนี้ได้")
        return

    channel = ctx.author.voice.channel
    await channel.connect()
    await ctx.send(f"เข้าร่วมช่องเสียง: {channel.name}")


# คำสั่ง !play_yt [url]: ให้บอทเล่นเพลงจากลิงก์ YouTube
@bot.command(name='play')
async def play_yt(ctx, url: str):
    if not ctx.voice_client:
        await ctx.send("บอทยังไม่ได้อยู่ในช่องเสียง โปรดใช้คำสั่ง !join ก่อน")
        return

    ctx.voice_client.stop()

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['url']

        ctx.voice_client.play(discord.FFmpegPCMAudio(url2, executable=FFMPEG_PATH))
        await ctx.send(f"กำลังเล่นเพลงจาก YouTube: {info['title']}")

    except yt_dlp.utils.DownloadError:
        await ctx.send("ไม่สามารถดึงข้อมูลวิดีโอจากลิงก์ได้ กรุณาตรวจสอบลิงก์อีกครั้ง (อาจไม่ใช่ลิงก์วิดีโอเดี่ยว)")
    except Exception as e:
        await ctx.send(f"เกิดข้อผิดพลาดในการเล่นเพลง: {e}")


# คำสั่ง !play_spotify [ชื่อเพลง]: ให้บอทเล่นเพลงจาก Spotify
@bot.command(name='spotify')
async def play_spotify(ctx, *, song_name: str):
    if not ctx.voice_client:
        await ctx.send("บอทยังไม่ได้อยู่ในช่องเสียง โปรดใช้คำสั่ง !join ก่อน")
        return

    if sp is None:
        await ctx.send("ไม่สามารถเชื่อมต่อ Spotify API ได้ โปรดตรวจสอบ Client ID และ Client Secret")
        return

    ctx.voice_client.stop()

    try:
        results = sp.search(q=song_name, limit=1, type='track')
        if not results['tracks']['items']:
            await ctx.send(f"ไม่พบเพลง '{song_name}' ใน Spotify")
            return

        track = results['tracks']['items'][0]
        artist = track['artists'][0]['name']
        title = track['name']
        query = f"{title} {artist}"
        await ctx.send(f"ค้นหาเพลง: {query} ใน YouTube...")

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)
            url2 = info['entries'][0]['url']

        ctx.voice_client.play(discord.FFmpegPCMAudio(url2, executable=FFMPEG_PATH))
        await ctx.send(f"กำลังเล่นเพลง: {title} by {artist}")

    except Exception as e:
        await ctx.send(f"เกิดข้อผิดพลาดในการเล่นเพลง: {e}")


# คำสั่ง !leave: ให้บอทออกจากช่องเสียง
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("ออกจากช่องเสียงแล้ว")
    else:
        await ctx.send("บอทไม่ได้อยู่ในช่องเสียง")


# รัน Bot ด้วย Token ที่ได้จาก Discord Developer Portal
bot.run(BOT_TOKEN)