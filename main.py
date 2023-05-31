import csv
import os
import random

import requests
from discord.ext import commands

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
      # GASのAPIを叩く
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
    await message.reply(reply_msg)

bot.run(TOKEN)
