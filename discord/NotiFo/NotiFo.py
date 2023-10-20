import asyncio
import discord
import datetime
import pytz
import pymongo
import tracemalloc
from discord.ext import commands
from discord import app_commands
from discord.ext import tasks
# from discord.ui import View


bot = commands.Bot(command_prefix = 'who can find this?', intents = discord.Intents.all())
token = ''

tracemalloc.start()


# DB 생성 (document), 콜렉션 생성
client = pymongo.MongoClient("mongodb://localhost:27017/")

mydb = client["NotiFo_DB"]
ContentDateCol = mydb["ContentDate"]



# 봇 활성화
@bot.event
async def on_ready() :
    print(f'Bot name: {bot.user.name}')
    print('Successful for activating!')
    game = discord.Game('"/note"을 통해 일정 공지')
    await bot.change_presence(status = discord.Status.online, activity = game)

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error: {e}")



# 봇 전용 카테고리, 채널 자동 생성
@bot.event
async def on_guild_join(guild):

    print("asdf")
    noteCategory = await guild.create_category(name = '알림 봇')
    await guild.create_text_channel(name = '일정', category = noteCategory)



# 명령어
contentDic = {}
firstActive = False
cooltime = 0
DBdic = {}
# noteTitle = ''



# 봇 전용 채팅 채널 커스텀 생성 (보류)



# 일정 추가
@bot.tree.command(name = "note", description = "일정을 기록합니다.")
@app_commands.describe(content = "일정의 간단한 내용 입력")
@app_commands.describe(year = "일정의 년도 입력")
@app_commands.describe(month = "일정의 달 입력")
@app_commands.describe(day = "일정의 일 입력")
@app_commands.describe(hour = "일정의 시 입력")
@app_commands.describe(minute = "일정의 분 입력")

async def note(interaction: discord.Interaction, content: str, year: int, month: int, day: int, hour: int, minute: int):

    global contentDic
    global firstActive
    global cooltime
    global DBdic
    # global noteTitle

    if cooltime >= 5:

        try:

            # 유닉스 시간 변환
            datetimeOfContent = datetime.datetime(year, month, day, hour, minute, 0)
            unixtime = int(datetimeOfContent.timestamp())

            # 딕셔너리에 내용, 기간 저장
            contentDic[content] = unixtime

            contentDic = dict(sorted(contentDic.items(), key = lambda x: x[1]))

            # 임베드 생성 및 출력
            embed = discord.Embed(title = '일정', timestamp = datetime.datetime.now(pytz.timezone('UTC')), color = 0x09cf6a)
            embed.add_field(name = '', value = '', inline = False)
            embed.set_footer(text = '마지막 수정')

            for i in list(contentDic.keys()):
                embed.add_field(name = i, value = f'<t:{contentDic[i]}:R>', inline = False)
                embed.add_field(name = '', value = '', inline = False)


            if firstActive == False:
                await interaction.response.send_message(embed = embed)
                firstActive = True

            else:
                await interaction.channel.purge(limit = 1)
                await interaction.response.send_message(embed = embed)


            # DB에 저장



        except Exception as e:

            print(f"Error: {e}")
            cooltime = 0

            embed = discord.Embed(title = '오류', description = '날짜가 올바르지 않습니다!',
                                  timestamp = datetime.datetime.now(pytz.timezone('UTC')), color = 0xff3f3f)
            await interaction.response.send_message(embed = embed)

            await asyncio.sleep(3)
            await interaction.channel.purge(limit = 1)


    else:

        cooltime = 0

        embed = discord.Embed(title = '오류', description = f"5초 뒤에 다시 시도해주세요!",
                              timestamp = datetime.datetime.now(pytz.timezone('UTC')), color = 0xff3f3f)
        await interaction.response.send_message(embed = embed)

        await asyncio.sleep(3)
        await interaction.channel.purge(limit = 1)



# 일정 삭제
@bot.tree.command(name = "delete", description = "일정을 수동으로 삭제합니다.")
async def delete(interaction: discord.Interaction, content: str):

    global contentDic
    global firstActive
    global cooltime
    # global noteTitle

    if cooltime >= 5:

        try:

            del contentDic[content]

            embed = discord.Embed(title = '일정', timestamp = datetime.datetime.now(pytz.timezone('UTC')), color = 0x09cf6a)
            embed.add_field(name = '', value = '', inline = False)
            embed.set_footer(text = '마지막 수정')

            for i in list(contentDic.keys()):
                embed.add_field(name = i, value = f'<t:{contentDic[i]}:R>', inline = False)
                embed.add_field(name = '', value = '', inline = False)

            if firstActive == False:
                await interaction.response.send_message(embed = embed)
                firstActive = True
            else:
                await interaction.channel.purge(limit = 1)
                await interaction.response.send_message(embed = embed)


        except Exception as e:

            print(f"Error: {e}")
            cooltime = 0

            embed = discord.Embed(title = '오류', description = "알 수 없는 이유로 오류가 발생했습니다!",
                                  timestamp = datetime.datetime.now(pytz.timezone('UTC')), color = 0xff3f3f)
            await interaction.response.send_message(embed = embed)

            await asyncio.sleep(3)
            await interaction.channel.purge(limit = 1)

    else:

        cooltime = 0

        embed = discord.Embed(title = '오류', description = f"5초 뒤에 다시 시도해주세요!",
                              timestamp = datetime.datetime.now(pytz.timezone('UTC')), color = 0xff3f3f)
        await interaction.response.send_message(embed = embed)

        await asyncio.sleep(3)
        await interaction.channel.purge(limit = 1)



# 기타 서버 관리 기능



# 쿨타임 루프
@tasks.loop()
async def cooltime_loop():

    global cooltime

    await asyncio.sleep(1)
    cooltime += 1



async def run_bot():
    cooltime_loop.start()
    # auto_delete_loop.start()
    await bot.start(token)

if __name__ == '__main__':
    asyncio.run(run_bot())



bot.run(token)