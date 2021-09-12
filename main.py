import random
from discord.ext import commands
import requests
import csv
import os
import youtube_dl

try:
  from local_settings import *
except ImportError:
  print("No local settings found")
  TOKEN = os.environ.get('TOKEN')
  APIURL = os.environ.get('APIURL')

lang, lang_code = [], []
with open("translate_lang.csv", "r", encoding="utf-8") as f:
  reader = csv.reader(f)
  for row in reader:
    lang.append(row[0])
    lang_code.append(row[1])

translate_langs = "ja,en,ja"

# youtube dl
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

bot = commands.Bot(command_prefix='/')


@bot.event
async def on_ready():
  print("bot started")

@bot.event
async def on_message(message):
  global translate_langs
  if message.author.bot:
    return
  elif message.content.startswith("http"):
    return
  elif message.content.startswith("/set"):  # /set
    for l in message.content.split(",")[1:]:
      if not l in lang_code:
        await message.channel.send("Language not found : {}".format(l))
        return
    translate_langs = ",".join(message.content.split(" ")[1:])
    await message.channel.send("successfully set the setting to {}".format(translate_langs))
  elif message.content.startswith("/rand"): # /rand
    num = int(message.content.split(" ")[1])
    if 1 <= num and num <= 10:
      translate_langs = "ja," + ",".join(random.choices(lang_code, k=num)) + ",ja"
      await message.channel.send("successfully set the setting to {}".format(translate_langs))
    else:
      await message.channel.send("error : /rand >>>{}<<<  Please enter a number between 1 and 10".format(num))
  elif message.content.startswith("/bot"): # /bot
    await message.channel.send("current translate rule: {}".format(translate_langs))
  elif message.content.startswith("/langlist"): # /langlist
    msg = "言語 : 言語コード\n"
    for i in range(len(lang)):
      msg += "{} : {}\n".format(lang[i], lang_code[i])
    await message.channel.send(msg)
  elif message.content.startswith("/help"): # /help
    await message.channel.send(
      "/set [langs] : 翻訳する順番の設定 ex.) /set ja en de ja\n"+
      "/bot : 現在のボットの設定\n" +
      "/help : コマンドについての説明を表示する\n" +
      "/langlist : 使うことのできる言語コードを表示する\n"+
      "/rand [int: num] : ランダムで言語を設定する 0 < num < 10 ex.) /rand 3"
    )
  elif message.content.startswith("/t"): # /translate
    msg = "".join(message.content.split(" ")[1:])
    try:
      translate_msg = requests.get(APIURL.format(msg, translate_langs)).json()["text"].split(",,,,,")
      reply_msg = ""
      for i, (m, l) in enumerate(zip(translate_msg, translate_langs.split(","))):
        if i != len(translate_msg) - 1:
          reply_msg += lang[lang_code.index(l)] + ":" + m + "\n↓\n"
        else:
          reply_msg += lang[lang_code.index(l)] + ":" + m
    except:
      await message.channel.send("error : {}".format("Please reset lang set"))
      return
    # print(msg + " -> " + translate_msg)
    await message.reply(reply_msg)
    # await message.channel.send(translate_msg)
  # youtube
  elif message.content.startswith('/join'):
    if message.author.voice is None:
      await message.channel.send("あなたはボイスチャンネルに接続していません。")
    else:
      await message.author.voice.channel.connect()
  elif message.content.startswith("/leave"):
    if message.guild.voice_client is None:
      await message.channel.send("ボイスチャンネルに接続していません。")
    else:
      await message.guild.voice_client.disconnect()
  elif message.content.startswith("/play"):
    if message.guild.voice_client is None:
      await message.channel.send("接続していません。")
    else:
      url = message.content.split(" ")[1]
      player = await YTDLSource.from_url(url, loop=bot.loop)
      await message.guild.voice_client.play(player)
      await message.channel.send('{} を再生します。'.format(player.title))
  else:
    return

bot.run(TOKEN)