import asyncio
import discord
import datetime
import pytz
import tracemalloc
import pymongo
from discord.ext import commands
from discord import app_commands
from discord.ext import tasks


bot = commands.Bot(command_prefix = 'who can find this?', intents = discord.Intents.all())
token = ''

tracemalloc.start()


# DB 생성 (document), 콜렉션 생성
client = pymongo.MongoClient("mongodb://localhost:27017/")

mydb = client["NotiFo_DB"]

if "ContentDate" not in mydb.list_collection_names():
    mydb.create_collection("ContentDate")

ContentDateCol = mydb["ContentDate"]



# 1. 할 거
    # 1. 오류창 5초동안만 보이게 하는 거 (3초로 변경, 완료)
    # 2. 날짜 오류 범위 정교화 (완료)
    # 3. 봇 전용 채널 자동 생성 (완료)
    # 4. 메세지 삭제시킬 때 임베드 메세지인지 확인하고 삭제 (실패)
    # 5. 임베드 제목 커스텀 (4번 없이는 불가)
    # 6. 기간 지나면 자동 삭제 (실패, 없어도 크게 문제될 것 없어 보류)
    # 7. 쿨타임 설정 (완료)
    # 8. 아마?도 이게 끝

# 2. 고쳐야 할거
    # 1. 1-4를 안하면 한 챗채널에서 여러 개를 쓸 수 없음
    # 2. 1-2 실패 (사유: 함수 작동 안됨, 단순히 복붙해서 쭉 나열하면 해결되긴 할텐데 코드꼴 보기 싫어질 듯) > 2023.2.28 오류 수정
    # 3. 오류 임베드가 출력되었을 때 삭제되기 전까지의 시간인 3초 안에 명령어를 또 실행시키면 다른 임베드가 지워지는 오류 발생, 1-7를 해야하는 이유 > 2023.2.28 오류 수정

# 3. 추가할 거
    # 1. 슬래시 커맨드 버튼을 통해 dm으로 알림 설정
    # 2. 일정 개수에 따라 임베드 색 교체
    # 3. 봇 24시간 호스팅



# 봇 활성화
@bot.event
async def on_ready() :
    print(f'Bot name: {bot.user.name}')
    print('Successful for activating!')
    game = discord.Game('테스트 중')
    await bot.change_presence(status = discord.Status.do_not_disturb, activity = game)

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
DBdic = {} # ex) { guild.id : [[content, int(unixtime)],[content22, int(unixtime22)]], guild22.id : [[content, int(unixtime)],[content22, int(unixtime22)]] }
cooltime = 0
tempBool = False
# noteTitle = ''



# 봇 전용 채팅 채널 커스텀 생성 (보류)
'''
@bot.tree.command(name = "create", description = "알림 봇 전용 채팅 채널을 생성합니다.")
@app_commands.describe(title = "채팅 채널, 알림 임베드 이름 설정")

async def create(interaction: discord.Interaction, title: str):

    global noteTitle
    global noteCategory

    noteTitle = title
    await interaction.guild.create_text_channel(name = noteTitle, category = noteCategory)
'''



# 일정 추가
@bot.tree.command(name = "note", description = "일정을 기록합니다.")
@app_commands.describe(content = "일정의 간단한 내용 입력")
@app_commands.describe(year = "일정의 년도 입력")
@app_commands.describe(month = "일정의 달 입력")
@app_commands.describe(day = "일정의 일 입력")
@app_commands.describe(hour = "일정의 시 입력")
@app_commands.describe(minute = "일정의 분 입력")

async def note(interaction: discord.Interaction, content: str, year: int, month: int, day: int, hour: int, minute: int):

    global DBdic
    global cooltime
    global tempBool
    # global noteTitle

    if cooltime >= 5:

        try:

            # 유닉스 시간 변환
            datetimeOfContent = datetime.datetime(year, month, day, hour, minute, 0)
            unixtime = int(datetimeOfContent.timestamp())

            # 딕셔너리에 내용, 기간 저장
            for i in DBdic:

                if i == interaction.guild.id:

                    DBdic[interaction.guild.id].append([content, int(unixtime)])
                    tempBool = True
                    break

            # DBdic에 명령어를 실행한 서버의 id가 없을 때 -> 실행한 서버에서 최초로 명령어를 실행했을 때
            if tempBool == False:
                DBdic[interaction.guild.id] = [[content, int(unixtime)]]


            # 임베드 생성 및 출력
            embed = discord.Embed(title = '일정', timestamp = datetime.datetime.now(pytz.timezone('UTC')), color = 0x09cf6a)
            embed.add_field(name = '', value = '', inline = False)
            embed.set_footer(text = '마지막 수정')

            for i in list(DBdic.keys()):

                if i == interaction.guild.id:

                    embed.add_field(name = DBdic[i][len(DBdic[i]) - 1][0], value = f'<t:{DBdic[i][len(DBdic[i]) - 1][1]}:R>', inline = False)
                    embed.add_field(name = '', value = '', inline = False)

                    DBdic[i] = sorted(DBdic[i], key = lambda x: x[1]) # 날짜 순으로 정렬

                    break

            await interaction.channel.purge(limit = 1)
            await interaction.response.send_message(embed = embed)



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

    global DBdic
    global cooltime
    # global noteTitle

    if cooltime >= 5:

        try:

            del DBdic[content]

            embed = discord.Embed(title = '일정', timestamp = datetime.datetime.now(pytz.timezone('UTC')), color = 0x09cf6a)
            embed.add_field(name = '', value = '', inline = False)
            embed.set_footer(text = '마지막 수정')

            for i in list(DBdic.keys()):
                embed.add_field(name = i, value = f'<t:{DBdic[i]}:R>', inline = False)
                embed.add_field(name = '', value = '', inline = False)

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

# 채팅 클리어

class message_delete_all(discord.ui.View):

    def __init__(self):
        super().__init__()


    @discord.ui.button(style = discord.ButtonStyle.green, label = "확인")
    async def on_interaction_confirm(self, interaction: discord.Interaction):

        await interaction.response.defer()

        await interaction.channel.purge(limit = None).flattened()

        global cooltime
        cooltime = 0

        embed = discord.Embed(title = '완료', description = "성공적으로 모든 메세지를 삭제했습니다!",
                                  timestamp = datetime.datetime.now(pytz.timezone('UTC')), color = 0x09cf6a)
        await interaction.response.send_message(embed = embed)

        await asyncio.sleep(3)
        await interaction.channel.purge(limit = 1)


    @discord.ui.button(style = discord.ButtonStyle.red, label = "취소")
    async def on_interaction_cancel(self, interaction: discord.Interaction):

        await interaction.response.defer()
        await interaction.channel.purge(limit = 1)

        global cooltime
        cooltime = 0

        embed = discord.Embed(title = '완료', description = "취소했습니다!",
                              timestamp = datetime.datetime.now(pytz.timezone('UTC')), color = 0x09cf6a)
        await interaction.response.send_message(embed = embed)

        await asyncio.sleep(3)
        await interaction.channel.purge(limit = 1)



@bot.tree.command(name = "clear", description = "설정한 수만큼의 메세지를 삭제합니다.")
@app_commands.describe(number = "삭제할 메세지의 수 입력 / all 입력시 모든 메세지 삭제")

async def clear(interaction: discord.Interaction, number: str):

    global cooltime

    if cooltime >= 5:

        try:

            if number == "all":

                view = message_delete_all()
                cooltime = 0

                embed = discord.Embed(title = '주의', description="정말로 모든 메세지를 삭제하겠습니까?",
                                      timestamp = datetime.datetime.now(pytz.timezone('UTC')), color = 0xfff861)
                await interaction.response.send_message(embed = embed, view = view)

            else:

                await interaction.response.defer()
                await interaction.channel.purge(limit = int(number) + 1)

                cooltime = 0


        except Exception as e:

            print(f"Error: {e}")
            cooltime = 0

            embed = discord.Embed(title = '오류', description = "올바른 값을 입력했는지 확인해주세요!",
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



# test
@bot.tree.command(name = "print_var", description = "print var, dic, etc (not all)")
async def print_var(interaction: discord.Interaction):

    global DBdic
    global cooltime

    if interaction.user.id == 420898823557218305:

        cooltime = 0

        await interaction.response.send_message(f'DBdic: {DBdic}\r'
                                                f'cooltime: {cooltime}')

    else:

        cooltime = 0

        embed = discord.Embed(title = '오류', description = '이 명령어를 사용할 권한이 없습니다!',
                              timestamp = datetime.datetime.now(pytz.timezone('UTC')), color = 0xff3f3f)
        await interaction.response.send_message(embed = embed)

        await asyncio.sleep(3)
        await interaction.channel.purge(limit = 1)



# 봇 종료
@bot.tree.command(name = "shutdown", description = "shutting down bot")
async def shutdown(interaction: discord.Interaction):

    global cooltime

    if interaction.user.id == 420898823557218305:

        print("Shutting down!")
        await bot.close()

    else:

        cooltime = 0

        embed = discord.Embed(title = '오류', description = '이 명령어를 사용할 권한이 없습니다!',
                              timestamp = datetime.datetime.now(pytz.timezone('UTC')), color = 0xff3f3f)
        await interaction.response.send_message(embed = embed)

        await asyncio.sleep(3)
        await interaction.channel.purge(limit = 1)



# 쿨타임 루프
@tasks.loop()
async def cooltime_loop():

    global cooltime

    await asyncio.sleep(1)
    cooltime += 1



# 일정 자동 삭제 (보류)
'''
@tasks.loop()
async def auto_delete_loop(ctx):

    global DBdic

    await asyncio.sleep(1)

    for i in list(DBdic.keys()):
        if int(DBdic[i]) == int(datetime.datetime(datetime.datetime.now(pytz.timezone('UTC')).year,
                                                  datetime.datetime.now(pytz.timezone('UTC')).month,
                                                  datetime.datetime.now(pytz.timezone('UTC')).day,
                                                  datetime.datetime.now(pytz.timezone('UTC')).hour,
                                                  datetime.datetime.now(pytz.timezone('UTC')).minute, 0).timestamp()) - 1:

            del DBdic[i]

            embed = discord.Embed(title = '일정', timestamp = datetime.datetime.now(pytz.timezone('UTC')), color = 0x09cf6a)
            embed.add_field(name = '', value = '', inline = False)
            embed.set_footer(text = '마지막 수정')

            for j in list(DBdic.keys()):
                embed.add_field(name = j, value = f'<t:{DBdic[j]}:R>', inline = False)
                embed.add_field(name = '', value = '', inline = False)

            await ctx.channel.purge(limit = 1)
            await ctx.send(embed = embed)
'''



# 봇 종료될 때 DBdic에 있는 값을 저장
@bot.event
async def on_shutdown():

    global ContentDateCol
    global DBdic

    ContentDateCol.insert_many(DBdic)

    await asyncio.sleep(5)



async def run_bot():
    cooltime_loop.start()
    # auto_delete_loop.start()
    await bot.start(token)

if __name__ == '__main__':
    asyncio.run(run_bot())