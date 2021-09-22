'''
DISCORD MUSIC BOT - CSN 

Version:    1.0.1
Author:     BaoLT
Github:     https://github.com/luthebao
Website:    https://luthebao.com
Bot này được viết dành tặng cho Cam 🍊 - VUI LÒNG GHI NGUỒN KHI SỬ DỤNG BOT
'''


import discord
import requests
import bs4
import asyncio
import datetime, random, json
from discord.ext import commands

prefix = "b."
discord_token = "THAY TOKEN O DAY"

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("help")
        self.is_playing = False
        self.music_queue = []
        self.loop = False
        self.datafile = "data.json"
        self.csnaccount = {
            "email": "",
            "password": "",
            "remember": "true",
        }
        self.indexing = 0
        self.lastupdate = 0
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        self.vc = ""

    def search_zmp3(self, item, index=0):
        with requests.Session() as ss:
            try:
                if "http" in item and "zing" in item and "bai-hat" in item:
                    name = item
                    id = (item.split("/"))[-1].split(".htm")[0]
                    artist = "default"
                    thumb = "https://cdn.discordapp.com/avatars/850416535583719485/a7f70c1b32e1d91ea44e7ea8ef700b57.png"
                else:
                    info = ss.get(
                        url=f"http://ac.mp3.zing.vn/complete?type=song,key,code&num=500&query={item}",
                        headers={
                            "Upgrade-Insecure-Requests": "1",
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36 Edg/93.0.961.52"
                        }
                    )
                    name = info.json()["data"][0]["song"][index]["name"]
                    id = info.json()["data"][0]["song"][index]["id"]
                    artist = info.json()["data"][0]["song"][index]["artist"]
                    thumb = "https://photo-resize-zmp3.zadn.vn/w240_r1x1_jpeg/" + \
                        info.json()["data"][0]["song"][index]["thumb"]
            except Exception:
                return False

        return {
            'source': f"http://api.mp3.zing.vn/api/streaming/audio/{id}/128",
            'url': f"https://zingmp3.vn/link/song/{id}",
            'title': name,
            "artist": artist,
            "thumb": thumb
        }

    def search_csn(self, item, index=0):
        try:
            source = ""
            if "chiasenhac.vn/mp3/" in item:
                url = item
                abc = requests.get(url=url)
                sou1 = bs4.BeautifulSoup(abc.text, 'html.parser')
                gettile = sou1.find('meta', attrs={ 'name' : 'title' })['content']
                name = gettile.split("-")[0]
                artist = gettile.split("-")[-1]
                thumb = sou1.find('meta', attrs={ 'property' : 'og:image' })['content']
            else:    
                abc = requests.get("https://chiasenhac.vn/search/real?type=json&rows=10&view_all=true&q=" + item)
                result = abc.json()[0]["music"]["data"]
                aftersort = sorted(result, key=lambda k: k['music_listen'], reverse=True)
                name = aftersort[0]["music_title"]
                artist = aftersort[0]["music_artist"]
                thumb = aftersort[0]["music_cover"]
                url = aftersort[0]["music_link"]
            with requests.Session() as s1:
                log_token = s1.get("https://chiasenhac.vn/")
                beau1 = bs4.BeautifulSoup(log_token.text, "html.parser")
                csrf_token = beau1.find("meta", attrs={"name": "csrf-token"})
                login = s1.post(
                    url="https://chiasenhac.vn/login",
                    data=self.csnaccount,
                    headers={
                        "X-CSRF-TOKEN": csrf_token['content']
                    }
                )

                get2 = s1.get(url=url)

                beau2 = bs4.BeautifulSoup(get2.text, "html.parser")

                download_items = beau2.find_all( "a", attrs={"class": "download_item"})

                for x in download_items:
                    if x.has_attr("href") and "chiasenhac.com" in x['href'] and "/128/" in x['href']:
                        source = x['href']
                        break
        except Exception:
            return False
        if source == "":
            return False
        
        return {
            'source': source,
            'url': url,
            'title': name,
            "artist": artist,
            "thumb": thumb
        }

    def music_add(self, item):
        embed = discord.Embed(title=f"Đã thêm vào: {item['title']}", url=item['url'], color=0xffffff)
        embed.set_thumbnail(url=item['thumb'])
        embed.add_field(name="Tên bài hát", value=item['title'], inline=True)
        embed.add_field(name="Ca sĩ", value=item['artist'], inline=True)
        embed.set_footer(text="Bạn đang nghe nhạc từ bot của Cam Cute nhất đời 🍊")
        return embed

    def music_startPlay(self, item):
        embed = discord.Embed(title=f"Đang phát: {item['title']} - {item['artist']}", url=item['url'], color=0xffffff)
        embed.set_footer(text="Bạn đang nghe nhạc từ bot của Cam Cute nhất đời 🍊")
        return embed
        
    async def play_next(self, ctx):
        checknow = int(datetime.datetime.now().timestamp())
        self.lastupdate = checknow
        if len(self.music_queue) > 0:
            self.is_playing = True

            if self.loop:
                m_url = self.music_queue[self.indexing][0]['source']
                await ctx.send(embed=self.music_startPlay(self.music_queue[self.indexing][0]))
                self.indexing += 1
                if self.indexing >= len(self.music_queue):
                    self.indexing = 0
            else:
                m_url = self.music_queue[0][0]['source']
                await ctx.send(embed=self.music_startPlay(self.music_queue[0][0]))
                self.music_queue.pop(0)
            print("play next")
            self.vc.play(discord.FFmpegPCMAudio(source=m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
        else:
            self.is_playing = False
            if (ctx.voice_client):
                # await ctx.guild.voice_client.disconnect()
                await ctx.send(embed=discord.Embed(title=':stop_button: Đã chơi hết bài trong playlist.'))

    async def play_music(self, ctx):
        checknow = int(datetime.datetime.now().timestamp())
        self.lastupdate = checknow
        if len(self.music_queue) > 0:
            self.is_playing = True

            if self.loop:
                if self.indexing >= len(self.music_queue):
                    self.indexing = 0
                else:
                    self.indexing += 1
                m_url = self.music_queue[self.indexing][0]['source']
                await ctx.send(embed=self.music_startPlay(self.music_queue[self.indexing][0]))
                if self.vc == "" or not self.vc.is_connected() or self.vc == None:
                    self.vc = await self.music_queue[self.indexing][1].connect()
                else:
                    await self.vc.move_to(self.music_queue[self.indexing][1])
            else:
                m_url = self.music_queue[0][0]['source']
                await ctx.send(embed=self.music_startPlay(self.music_queue[0][0]))

                if self.vc == "" or not self.vc.is_connected() or self.vc == None:
                    self.vc = await self.music_queue[0][1].connect()
                else:
                    await self.vc.move_to(self.music_queue[0][1])
                self.music_queue.pop(0)
            print("play music")
            self.vc.play(discord.FFmpegPCMAudio(source=m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
        else:
            self.is_playing = False
            if (ctx.voice_client):
                await ctx.send(embed=discord.Embed(title=':stop_button: Đã chơi hết bài trong playlist.'))

    @commands.command(name="zmp3", help="chơi theo url, từ khoá với zingmp3")
    async def zing(self, ctx, *args):
        query = " ".join(args)

        embed = discord.Embed(title=f":hourglass_flowing_sand: Đang tìm: {query}", color=0xffffff)
        await ctx.send(embed=embed)

        voice_channel = ctx.author.voice.channel

        if voice_channel is None:
            await ctx.send(embed=discord.Embed(title="Bạn đang không ở trong kênh voice nào."))
        else:
            if len(ctx.bot.voice_clients) > 0 and ctx.bot.voice_clients[0].channel != voice_channel:
                await ctx.send(embed=discord.Embed(title="Bot đang được sử dụng ở kênh voice khác."))
                return
            try:
                index = int(args[-1])
            except:
                index = 0
            song = self.search_zmp3(query, index)
            if type(song) == type(True):
                await ctx.send(embed=discord.Embed(title="Không tìm được bài hát nào với từ khoá này."))
            else:
                await ctx.send(embed=self.music_add(song))

                self.music_queue.append([song, voice_channel])

                if self.is_playing == False:
                    await self.play_music(ctx)

    @commands.command(name="play", help="chơi theo từ khoá với chiasenhac", aliases=['p'])
    async def csn(self, ctx, *args):
        query = " ".join(args)

        embed = discord.Embed(
            title=f":hourglass_flowing_sand: Đang tìm: {query}", color=0xffffff)
        await ctx.send(embed=embed)

        voice_channel = ctx.author.voice.channel

        if voice_channel is None:
            # you need to be connected so that the bot knows where to go
            await ctx.send(embed=discord.Embed(title="Bạn đang không ở trong kênh voice nào."))
        else:
            if len(ctx.bot.voice_clients) > 0 and ctx.bot.voice_clients[0].channel != voice_channel:
                await ctx.send(embed=discord.Embed(title="Bot đang được sử dụng ở kênh voice khác."))
                return
            song = self.search_csn(query)
            if type(song) == type(True):
                await ctx.send(embed=discord.Embed(title="Không tìm được bài hát nào với từ khoá này."))
            else:
                await ctx.send(embed=self.music_add(song))

                self.music_queue.append([song, voice_channel])

                if self.is_playing == False:
                    await self.play_music(ctx)

    @commands.command(name="search", help="tìm kiếm trên chiasenhac")
    async def search(self, ctx, *args):
        try:
            query = " ".join(args[0:args.index("--max")])
        except:
            query = " ".join(args)

        maxs = 10
        try:
            if args.index("--max") > 0:
                maxs = int(args[-1])
        except:
            maxs = 10
        if maxs > 10:
            maxs = 10

        embed = discord.Embed(
            title=f":hourglass_flowing_sand: Đang tìm: {query}", color=0xffffff)
        await ctx.send(embed=embed)

        try: voice_channel = ctx.author.voice.channel
        except: 
            await ctx.send(embed=discord.Embed(title="Bạn đang không ở trong kênh voice nào."))
            return
        if voice_channel is None:
            await ctx.send(embed=discord.Embed(title="Bạn đang không ở trong kênh voice nào."))
        else:
            if len(ctx.bot.voice_clients) > 0 and ctx.bot.voice_clients[0].channel != voice_channel:
                await ctx.send(embed=discord.Embed(title="Bot đang được sử dụng ở kênh voice khác."))
                return
            abc = requests.get(f"https://chiasenhac.vn/search/real?type=json&rows={maxs}&view_all=true&q=" + query)
            result = abc.json()[0]["music"]["data"]
            msg = await ctx.send(embed=discord.Embed(title="React số để chọn bài hát", description="Chờ 1 lát ...",color=0xffffff))
            reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟', '🔇']
            
            embed = discord.Embed(title="React số để chọn bài hát", color=0xffffff)
            for i in range(0, len(result)):
                embed.add_field(name=f"{i+1}, {result[i]['music_title']} bởi {result[i]['music_artist']}", value=f"Link gốc: {result[i]['music_link']}", inline=False)
                await msg.add_reaction(reactions[i])
            embed.set_footer(text="Bạn đang nghe nhạc từ bot của Cam Cute nhất đời 🍊")
            await msg.add_reaction(reactions[-1])
            await msg.edit(embed=embed)

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in reactions
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            except asyncio.TimeoutError:
                await msg.edit(embed=discord.Embed(title="Hết thời gian chờ, vui lòng thử lại.", color=0xffffff))
            else:
                if str(reaction.emoji) == reactions[-1]:
                    await msg.edit(embed=discord.Embed(title="Đã tạm dừng tìm kiếm.", color=0xffffff))
                    return
                
                index = reactions.index(str(reaction.emoji))
                name = result[index]["music_title"]
                artist = result[index]["music_artist"]
                await msg.edit(embed=discord.Embed(title=f"Bạn đã chọn {name} - {artist}.", description="Vui lòng đợi trong giây lát ...", color=0xffffff))
                url = result[index]["music_link"]
                song = self.search_csn(url)
                await msg.delete()
                if type(song) == type(True):
                    await ctx.send(embed=discord.Embed(title="Không thể chơi được bài này vào lúc này."))
                else:
                    await ctx.send(embed=self.music_add(song))
                    self.music_queue.append([song, voice_channel])
                    if self.is_playing == False:
                        await self.play_music(ctx)

    @commands.command(name="queue", help="hiển thị playlist hiện tại", aliases=['q'])
    async def queue(self, ctx):
        if ctx.author.voice.channel is None or len(ctx.bot.voice_clients) > 0 and ctx.bot.voice_clients[0].channel != ctx.author.voice.channel:
            await ctx.send(embed=discord.Embed(title="Bot đang được sử dụng ở kênh voice khác."))
            return
        if len(self.music_queue) > 0:
            embed = discord.Embed(title="Playlist", color=0xffffff)
            for i in range(0, len(self.music_queue)):
                embed.add_field(name=f"{i+1}, {self.music_queue[i][0]['title']} bởi {self.music_queue[i][0]['artist']}", value=f"Link gốc: {self.music_queue[i][0]['url']}", inline=False)
            embed.set_footer(text="Bạn đang nghe nhạc từ bot của Cam Cute nhất đời 🍊")
            await ctx.send(embed=embed)

        else:
            await ctx.send(embed=discord.Embed(title="Không có bài nào trong playlist"))

    @commands.command(name="skip", help="chuyển sang bài kế tiếp", aliases=['s'])
    async def skip(self, ctx):
        if ctx.author.voice.channel is None or len(ctx.bot.voice_clients) > 0 and ctx.bot.voice_clients[0].channel != ctx.author.voice.channel:
            await ctx.send(embed=discord.Embed(title="Bot đang được sử dụng ở kênh voice khác."))
            return
        if self.vc != "" and self.vc:
            self.vc.stop()
            # await self.play_next(ctx)

    @commands.command(name="pause", help="tạm dừng bài hát")
    async def pause(self, ctx):
        if ctx.author.voice.channel is None or len(ctx.bot.voice_clients) > 0 and ctx.bot.voice_clients[0].channel != ctx.author.voice.channel:
            await ctx.send(embed=discord.Embed(title="Bot đang được sử dụng ở kênh voice khác."))
            return
        self.vc.pause()
        await ctx.send(embed=discord.Embed(title='Đã tạm dừng :pause_button:'))

    @commands.command(name="resume", help="tiếp tục bài hát")
    async def resume(self, ctx):
        if ctx.author.voice.channel is None or len(ctx.bot.voice_clients) > 0 and ctx.bot.voice_clients[0].channel != ctx.author.voice.channel:
            await ctx.send(embed=discord.Embed(title="Bot đang được sử dụng ở kênh voice khác."))
            return
        self.vc.resume()
        await ctx.send(embed=discord.Embed(title='Đã phát lại :arrow_forward:'))

    @commands.command(name="leave", help="rời khỏi kênh voice")
    async def leave(self, ctx):
        if ctx.author.voice.channel is None or len(ctx.bot.voice_clients) > 0 and ctx.bot.voice_clients[0].channel != ctx.author.voice.channel:
            await ctx.send(embed=discord.Embed(title="Bot đang được sử dụng ở kênh voice khác."))
            return
        if self.vc != "" and self.vc:
            self.music_queue = []
            self.vc.stop()
        if (ctx.voice_client):
            await ctx.guild.voice_client.disconnect()
            await ctx.send(embed=discord.Embed(title='Đã rời khỏi kênh.'))
        else:
            await ctx.send(embed=discord.Embed(title="Bot đang không đƯợc sử dụng nên không thể dùng lệnh này."))

    @commands.command(name="remove", help="xoá một bài hát trong playlist")
    async def remove(self, ctx, *args):
        if ctx.author.voice.channel is None or len(ctx.bot.voice_clients) > 0 and ctx.bot.voice_clients[0].channel != ctx.author.voice.channel:
            await ctx.send(embed=discord.Embed(title="Bot đang được sử dụng ở kênh voice khác."))
            return
        try:
            index = int(args[-1])
        except:
            index = 0
        if (ctx.voice_client):
            if len(self.music_queue) > 0 and index <= len(self.music_queue):
                self.music_queue.pop(index-1)
                await self.q(ctx)
            else:
                await ctx.send(embed=discord.Embed(title="Không có bài hát nào trong playlist"))
        else:
            await ctx.send(embed=discord.Embed(title="Bot đang không đƯợc sử dụng nên không thể dùng lệnh này."))

    @commands.command(name="shuffle", help="trộn ngẫu nhiên playlist")
    async def shuffle(self, ctx, *args):
        if ctx.author.voice.channel is None or len(ctx.bot.voice_clients) > 0 and ctx.bot.voice_clients[0].channel != ctx.author.voice.channel:
            await ctx.send(embed=discord.Embed(title="Bot đang được sử dụng ở kênh voice khác."))
            return
        try:
            index = int(args[-1])
        except:
            index = 0
        if (ctx.voice_client):
            if len(self.music_queue) > 0:
                playlist = self.music_queue
                random.shuffle(playlist)
                self.music_queue = playlist
                embed = discord.Embed(title="New playlist", color=0xffffff)
                for i in range(0, len(self.music_queue)):
                    embed.add_field(name=f"{i+1}, {self.music_queue[i][0]['title']} bởi {self.music_queue[i][0]['artist']}", value=f"Link gốc: {self.music_queue[i][0]['url']}", inline=False)
                embed.set_footer(text="Bạn đang nghe nhạc từ bot của Cam Cute nhất đời 🍊")
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=discord.Embed(title="Không có bài hát nào trong playlist"))
        else:
            await ctx.send(embed=discord.Embed(title="Bot đang không đƯợc sử dụng nên không thể dùng lệnh này."))

    @commands.command(name="loopqueue", help="lặp toàn bộ playlist")
    async def loopq(self, ctx):
        if ctx.author.voice.channel is None or len(ctx.bot.voice_clients) > 0 and ctx.bot.voice_clients[0].channel != ctx.author.voice.channel:
            await ctx.send(embed=discord.Embed(title="Bot đang được sử dụng ở kênh voice khác."))
            return
        if len(self.music_queue) > 0 and self.loop == False:
            self.loop = True
            await ctx.send(embed=discord.Embed(title="Playlist đã được lặp."))
        elif len(self.music_queue) > 0 and self.loop == True:
            self.loop = False
            await ctx.send(embed=discord.Embed(title="Playlist đã huỷ lặp."))
        else:
            await ctx.send(embed=discord.Embed(title="Không có bài nào để lặp."))

    @commands.command(name="help", help="xem toàn bộ commands")
    async def help(self, ctx):
        embed = discord.Embed(title="Danh sách command", description=f"Prefix của bot là: {prefix}", color=0xffffff)
        for cmd in self.bot.commands:
            name = cmd.__original_kwargs__['name']
            if "aliases" in cmd.__original_kwargs__:
                name += ", " + ", ".join(cmd.__original_kwargs__['aliases'])
            embed.add_field(name=name, value=cmd.__original_kwargs__['help'], inline=True)
            # print(cmd.__original_kwargs__)
        embed.set_footer(text="Bạn đang nghe nhạc từ bot của Cam Cute nhất đời 🍊")
        await ctx.send(embed=embed)
    
    @commands.command(name="save", help="lưu playlist hiện tại")
    async def saveq(self, ctx):
        if ctx.author.voice.channel is None or len(ctx.bot.voice_clients) > 0 and ctx.bot.voice_clients[0].channel != ctx.author.voice.channel:
            await ctx.send(embed=discord.Embed(title="Bot đang được sử dụng ở kênh voice khác."))
            return
        if len(self.music_queue) > 0:
            with open(self.datafile, 'a+') as f: pass
            with open(self.datafile, 'r+') as f2:
                current = f2.read()
                a = {}
            with open(self.datafile, 'w') as f1:
                try:
                    a = json.loads(current)
                except: pass
                data = []
                for i in self.music_queue:
                    data.append(i[0]['url'])
                keyplaylist = str(int(datetime.datetime.now().timestamp()*1000000))
                a[str(ctx.author.id)] = {
                    "name" : str(ctx.author),
                    "key": keyplaylist,
                    "list" : data
                }
                json.dump(a, f1)
                await ctx.send(embed=discord.Embed(title=f"Đã lưu playlist hiện tại vào hệ thống. Key của playlist: {keyplaylist}"))
                return
        else:
            await ctx.send(embed=discord.Embed(title="Không có bài nào trong playlist để lưu."))

    @commands.command(name="data", help="xem playlist gần nhất đã lưu")
    async def data(self, ctx):
        with open(self.datafile, 'a+') as f: pass
        with open(self.datafile, 'r') as f2:
            msg = await ctx.send(embed=discord.Embed(title="Đang load lại playlist từ hệ thống ..."))
            current = f2.read()
            try:
                a = json.loads(current)
            except: pass
            data = []
            if str(ctx.author.id) in a:
                data = a[str(ctx.author.id)]["list"]
            if len(data) > 0:
                embed = discord.Embed(title=f"Playlist đã lưu gần đây: {a[str(ctx.author.id)]['key']}", color=0xffffff)
                for i in range(0, len(data)):
                    song = self.search_csn(data[i])
                    embed.add_field(name=f"{i+1}, {song['title']} bởi {song['artist']}", value=f"Link gốc: {song['url']}", inline=False)
                embed.set_footer(text="Bạn đang nghe nhạc từ bot của Cam Cute nhất đời 🍊")
                await msg.edit(embed=embed)
            else:
                await msg.edit(embed=discord.Embed(title=f"Bạn không lưu playlist nào gần đây."))
            return
    
    @commands.command(name="loadq", help="phát lại playlist đã lưu")
    async def loadq(self, ctx, *args):
        if ctx.author.voice.channel is None or len(ctx.bot.voice_clients) > 0 and ctx.bot.voice_clients[0].channel != ctx.author.voice.channel:
            await ctx.send(embed=discord.Embed(title="Bot đang được sử dụng ở kênh voice khác."))
            return
        voice_channel = ctx.author.voice.channel

        if voice_channel is None:
            await ctx.send(embed=discord.Embed(title="Bạn đang không ở trong kênh voice nào."))
            return
        with open(self.datafile, 'a+') as f: pass
        with open(self.datafile, 'r') as f2:
            msg = await ctx.send(embed=discord.Embed(title="Đang load lại playlist từ hệ thống ..."))
            current = f2.read()
            try:
                a = json.loads(current)
            except: pass
            data = []
            if str(ctx.author.id) in a:
                data = a[str(ctx.author.id)]["list"]
            if len(data) > 0:
                queueload = []
                for i in range(0, len(data)):
                    song = self.search_csn(data[i])
                    if type(song) == type(True):
                        continue
                    else:
                        self.music_queue.append([song, voice_channel])
                        queueload.append([song, voice_channel])
                        if self.is_playing == False:
                            await self.play_music(ctx)
                self.music_queue = queueload
                self.loop = True
                await msg.edit(embed=discord.Embed(title=f"Đã load xong playlist vào queue hiện tại."))
            else:
                await msg.edit(embed=discord.Embed(title=f"Bạn không lưu playlist nào gần đây."))
            

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.bot.user == message.author and len(message.embeds) > 0 and ':stop_button:' in message.embeds[0].title:
            time = 0
            last = self.lastupdate
            while True:
                await asyncio.sleep(30)
                time = time + 1
                if last != self.lastupdate:
                    time = 0
                    break
                if time >= 6:
                    for vc in bot.voice_clients:
                        if vc.guild == message.guild:
                            await vc.disconnect()
                    await message.channel.send(embed=discord.Embed(title="Đã 3 phút không hoạt động, bot tự động rời khỏi kênh."))
                    break

bot = commands.Bot(command_prefix=prefix)
bot.add_cog(Music(bot))
print("=== BOT START ===")
bot.run(discord_token)
