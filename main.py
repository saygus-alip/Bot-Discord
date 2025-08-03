import discord
from discord.ext import commands
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import asyncio
from collections import deque

# 1. ตั้งค่า Spotify API Keys ของคุณ
# *** เปลี่ยน 'YOUR_SPOTIFY_CLIENT_ID' และ 'YOUR_SPOTIFY_CLIENT_SECRET' เป็นรหัสจริงของคุณ ***
SPOTIPY_CLIENT_ID = '653aff1d34b94289afeeca276fb0b879'
SPOTIPY_CLIENT_SECRET = '35c8f81113254613bb9640dd55dfe144'

# 2. ตั้งค่า Discord Bot Token ของคุณ
# *** เปลี่ยน 'YOUR_BOT_TOKEN' เป็น Token จริงของคุณ ***
BOT_TOKEN = 'MTQwMTQwMTQ4MTYzODQ0NTA2Ng.GKiyt9.JI7DZjaf4ChcD7Sd1wPd6nRaGnf1XtU7Ay_9-w'

# 3. ตั้งค่า FFmpeg executable
if os.path.exists("../ffmpeg.exe"):
    FFMPEG_PATH = "../ffmpeg.exe"
else:
    FFMPEG_PATH = "ffmpeg"

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

queues = {}
skip_votes = {}
ytdl_format_options = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

MANUAL_TEXT = """
### **คู่มือการใช้งานบอทเพลง**

คู่มือนี้จะช่วยให้คุณใช้งานบอทเพลงได้อย่างเข้าใจง่ายและเห็นภาพมากขึ้น

#### **1. คำสั่งพื้นฐาน (เริ่มต้นและจบการใช้งาน)**

| คำสั่ง | สิ่งที่คุณต้องพิมพ์ | สิ่งที่บอทจะตอบกลับ | การทำงานของบอท |
| :--- | :--- | :--- | :--- |
| **!join** | `!join` | เข้าร่วมช่องเสียง: **[ชื่อช่องเสียง]** | บอทจะเข้าร่วมช่องเสียงที่คุณอยู่ทันที |
| **!leave** | `!leave` | ออกจากช่องเสียงแล้ว | บอทจะออกจากช่องเสียงและลบเพลงในคิวทั้งหมด |

#### **2. คำสั่งสำหรับเล่นเพลง**

| คำสั่ง | สิ่งที่คุณต้องพิมพ์ | สิ่งที่บอทจะตอบกลับ | การทำงานของบอท |
| :--- | :--- | :--- | :--- |
| **!play [ชื่อเพลง]** | `!play สิทธิ์ของเธอ` | เพิ่มเพลง **สิทธิ์ของเธอ** เข้าสู่คิว | บอทจะค้นหาเพลงใน YouTube และเพิ่มเพลงเข้าไปในคิวเพลง |
| **!play [URL]** | `!play https://www.youtube.com/watch?v=48_PpIWeb6Y&list=RD48_PpIWeb6Y&start_radio=1` | เพิ่มเพลง **[ชื่อเพลง]** เข้าสู่คิว | บอทจะนำเพลงจากลิงก์ YouTube ที่คุณระบุมาใส่ในคิวเพลง |
| **!spotify [ชื่อเพลง]**| `!spotify all of me john legend` | ค้นหาเพลง: All of me John Legend ใน YouTube... \\n กำลังเล่นเพลง: **All of me** by **John Legend** | บอทจะค้นหาเพลงใน Spotify และนำเพลงที่เจอเพลงแรกมาเล่นจาก YouTube |

#### **3. คำสั่งสำหรับควบคุมเพลง**

| คำสั่ง | สิ่งที่คุณต้องพิมพ์ | สิ่งที่บอทจะตอบกลับ | การทำงานของบอท |
| :--- | :--- | :--- | :--- |
| **!pause** | `!pause` | หยุดเพลงชั่วคราวแล้ว | บอทจะหยุดเล่นเพลงที่คุณกำลังฟังอยู่ |
| **!resume** | `!resume` | เล่นเพลงต่อแล้ว | บอทจะเล่นเพลงต่อจากที่หยุดไว้ |
| **!skip** | `!skip` | โหวตข้ามเพลงแล้ว (1/3 โหวต) | สมาชิกในช่องเสียงทุกคนสามารถโหวตข้ามเพลงได้ เมื่อจำนวนโหวตถึงเกณฑ์ที่กำหนด บอทจะเล่นเพลงถัดไปในคิว |

#### **4. คำสั่งสำหรับจัดการคิวเพลง**

| คำสั่ง | สิ่งที่คุณต้องพิมพ์ | สิ่งที่บอทจะตอบกลับ | การทำงานของบอท |
| :--- | :--- | :--- | :--- |
| **!queue** | `!queue` | **รายการเพลงในคิว:** \\n 1. **[ชื่อเพลงที่กำลังเล่น]** \\n 2. **[ชื่อเพลงในคิว]** | บอทจะแสดงรายการเพลงที่อยู่ในคิวทั้งหมด |
"""


# ฟังก์ชันสำหรับเล่นเพลงถัดไปในคิว
async def play_next_song(ctx):
    guild_id = ctx.guild.id
    if guild_id in queues and queues[guild_id]:
        next_song = queues[guild_id].popleft()
        info = next_song['info']
        url = next_song['url']

        ctx.voice_client.play(
            discord.FFmpegPCMAudio(url, executable=FFMPEG_PATH),
            after=lambda e: bot.loop.create_task(play_next_song(ctx))
        )
        await ctx.send(f"กำลังเล่นเพลงถัดไป: **{info['title']}**")
    else:
        await asyncio.sleep(60)
        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            await ctx.voice_client.disconnect()


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    print('Bot is ready to go!')


@bot.command()
async def hello(ctx):
    await ctx.send(f'Hello! I am {bot.user.name}')


@bot.command(name='manual')
async def show_manual(ctx):
    await ctx.send(MANUAL_TEXT)


@bot.command()
async def join(ctx):
    if not ctx.author.voice:
        await ctx.send("คุณต้องอยู่ในช่องเสียงก่อนถึงจะใช้คำสั่งนี้ได้")
        return

    channel = ctx.author.voice.channel
    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()
    await ctx.send(f"เข้าร่วมช่องเสียง: **{channel.name}**")


@bot.command(name='play')
async def play_yt(ctx, *, query: str):
    if not ctx.voice_client:
        await ctx.send("บอทยังไม่ได้อยู่ในช่องเสียง โปรดใช้คำสั่ง `!join` ก่อน")
        return

    guild_id = ctx.guild.id
    if guild_id not in queues:
        queues[guild_id] = deque()

    try:
        with yt_dlp.YoutubeDL(ytdl_format_options) as ydl:
            if query.startswith("http"):
                info = ydl.extract_info(query, download=False)
            else:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]

            url2 = info['url']

        song_info = {
            'info': info,
            'url': url2
        }

        queues[guild_id].append(song_info)
        await ctx.send(f"เพิ่มเพลง **{info['title']}** เข้าสู่คิว")

        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            await play_next_song(ctx)

    except yt_dlp.utils.DownloadError:
        await ctx.send("ไม่สามารถดึงข้อมูลวิดีโอจากลิงก์ได้ กรุณาตรวจสอบลิงก์/ชื่อเพลงอีกครั้ง")
    except Exception as e:
        await ctx.send(f"เกิดข้อผิดพลาดในการเล่นเพลง: {e}")


@bot.command(name='spotify')
async def play_spotify(ctx, *, song_name: str):
    if not ctx.voice_client:
        await ctx.send("บอทยังไม่ได้อยู่ในช่องเสียง โปรดใช้คำสั่ง `!join` ก่อน")
        return

    if sp is None:
        await ctx.send("ไม่สามารถเชื่อมต่อ Spotify API ได้ โปรดตรวจสอบ Client ID และ Client Secret")
        return

    guild_id = ctx.guild.id
    if guild_id not in queues:
        queues[guild_id] = deque()

    try:
        results = sp.search(q=song_name, limit=1, type='track')
        if not results['tracks']['items']:
            await ctx.send(f"ไม่พบเพลง '{song_name}' ใน Spotify")
            return

        track = results['tracks']['items'][0]
        artist = track['artists'][0]['name']
        title = track['name']
        query = f"{title} {artist}"

        with yt_dlp.YoutubeDL(ytdl_format_options) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
            url2 = info['url']

        song_info = {
            'info': info,
            'url': url2
        }

        queues[guild_id].append(song_info)
        await ctx.send(f"เพิ่มเพลง **{title}** by **{artist}** เข้าสู่คิว")

        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            await play_next_song(ctx)

    except Exception as e:
        await ctx.send(f"เกิดข้อผิดพลาดในการเล่นเพลง: {e}")


@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("หยุดเพลงชั่วคราวแล้ว")
    else:
        await ctx.send("ไม่มีเพลงที่กำลังเล่นอยู่")


@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("เล่นเพลงต่อแล้ว")
    else:
        await ctx.send("ไม่มีเพลงที่หยุดชั่วคราวอยู่")


@bot.command()
async def skip(ctx):
    guild_id = ctx.guild.id
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await ctx.send("ไม่มีเพลงที่กำลังเล่นอยู่")
        return

    if guild_id not in skip_votes:
        skip_votes[guild_id] = set()

    skip_votes[guild_id].add(ctx.author.id)

    voice_channel_members = [member for member in ctx.voice_client.channel.members if not member.bot]
    required_votes = max(1, len(voice_channel_members) // 2)

    if len(skip_votes[guild_id]) >= required_votes:
        ctx.voice_client.stop()
        await ctx.send("ข้ามเพลงแล้ว! (โหวตครบ)")
        skip_votes[guild_id].clear()
    else:
        await ctx.send(f"โหวตข้ามเพลงแล้ว ({len(skip_votes[guild_id])}/{required_votes} โหวต)")


@bot.command()
async def queue(ctx):
    guild_id = ctx.guild.id
    if guild_id not in queues or not queues[guild_id]:
        await ctx.send("ไม่มีเพลงในคิว")
        return

    message = "**รายการเพลงในคิว:**\n"
    for i, song in enumerate(queues[guild_id]):
        message += f"{i + 1}. **{song['info']['title']}**\n"
        if i >= 9:
            message += f"และเพลงอื่นๆ อีก {len(queues[guild_id]) - 10} เพลง..."
            break
    await ctx.send(message)


@bot.command()
async def leave(ctx):
    guild_id = ctx.guild.id
    if ctx.voice_client:
        if guild_id in queues:
            queues[guild_id].clear()
        if guild_id in skip_votes:
            skip_votes[guild_id].clear()
        await ctx.voice_client.disconnect()
        await ctx.send("ออกจากช่องเสียงแล้ว")
    else:
        await ctx.send("บอทไม่ได้อยู่ในช่องเสียง")


# รัน Bot ด้วย Token ที่ได้จาก Discord Developer Portal
bot.run(BOT_TOKEN)