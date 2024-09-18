#!/usr/bin/env python3
import discord
from discord.ext import commands
import asyncio
import requests
from bs4 import BeautifulSoup
import os
import sys
from PIL import Image




admins = [167399259795095552,103987106732347392]


def is_compiled():
    return not "python.exe" in sys.executable
def clean_path(path):
    normalized_path = os.path.normpath(path)
    cleaned_path = normalized_path.strip(os.path.sep)
    return cleaned_path
def top_path():
    if (is_compiled()):
        return os.sep.join(sys.executable.split("\\")[:-1])
    else:
        return os.path.dirname(__file__).rstrip(os.sep +"cogs")

def rel_path(p = ""):
    return top_path() + os.sep + p

class Timer:
    def __init__(self):
        self.task = None

    async def _run(self, delay, callback, *args, **kwargs):
        await asyncio.sleep(delay)
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            print(f"Timer exception: {e}")

    def start(self, delay, callback, *args, **kwargs):
        if self.task is not None:
            self.task.cancel()
        self.task = asyncio.create_task(self._run(delay, callback, *args, **kwargs))

    def cancel(self):
        if self.task is not None:
            self.task.cancel()
            self.task = None

def distribute_cards(num_cards):
    row_distribution = []
    while num_cards >= 10:
        num_cards -= 10
        row_distribution.append(10)
    if(num_cards % 10 > 0):
        row_distribution.append(num_cards % 10)
    return row_distribution, len(row_distribution)

def get_card(d, i):
    expanded_list = []
    for key, count in d.items():
        expanded_list.extend([key] * count)
    if i > 0 and i <= len(expanded_list):
        return expanded_list[i - 1] 
    else:
        return None

def scrape(ttc_number):
    page = requests.get('https://tengutools.com/events/')
    soup = BeautifulSoup(page.text, 'html.parser')
    title = None
    wrapper = None
    block = None
    try:
        title = soup.find_all('strong',string=f"Toronto Time Capsule {ttc_number} Results")[0]
    except:
        print("Not found")
    if(title):
        try:
            wrapper = title.parent.parent.parent
        except:
            print("Parent div not found")
    if(wrapper):
        try:
            block = list(wrapper.children)[3]
        except:
            print("Failed to extract info from tournamnet")
    name,url,deck_name = (None, None, None)
    if(block):
        try:
            name = block.find('span').text
            link = block.find('a')
            url = link['href']
            deck_name = link.text
        except:
            print("Failed to parse name, title and url")
    if(name and url and deck_name):
        ydk = requests.get(f"https://tengutools.com/wp-content/uploads/decks/{url.split("?deck=")[1]}.ydk")
        #parse content
        cards = str(ydk.content).split("\\n")
        main_size = 0
        main = {}
        side = {}
        extra = {}
        all_ids = []
        mode = None
        for card in cards:
            if(card == "#main"):
                mode = main
            elif(card == "!side"):
                mode = side
            elif(card == "#extra"):
                mode = extra
            elif(mode != None):
                is_card = False
                try:
                    _ = int(card)
                    is_card = True
                except:
                    pass
                if(is_card):
                    if(mode == main):
                        main_size += 1
                    if(not card in all_ids):
                        all_ids.append(card)
                    if(card in mode):
                        mode[card] += 1
                    else:
                        mode[card] = 1
        # fetch images from tengutools
        for card_id in all_ids:
            if(not os.path.isfile(rel_path("db"+os.sep+card_id+".jpg"))):
                img = requests.get(f"https://tengutools.com/wp-content/uploads/pictures/cards/{card_id.lstrip("0")}.jpg")
                with open(rel_path("db"+os.sep+card_id+".jpg"),"wb") as f:
                    f.write(img.content)
                    print(f"downloaded {card_id}")

        #make the image

        per_row, cols = distribute_cards(main_size)
        padding = 8
        small_factor = 1/1.5
        c_width = 421
        c_height = 614

        t_width = (c_width + padding) * per_row[0]
        t_height = (c_height + padding) * cols
        t_height += int(((c_height + padding) * 2) * small_factor)

        #main
        img = Image.new('RGB', (t_width, t_height) , color = 'black')
        card_count = 1
        for i in range(0,cols):
            h_offset = int(padding/2)+(i*(c_height+padding))
            for j in range(0,per_row[i]):
                w_offset = int(padding/2)+(j*(c_width+padding))
                card_id = get_card(main, card_count)
                card_count += 1
                if(card_id):
                    card_img = Image.open(rel_path("db"+os.sep+card_id+".jpg"))
                    img.paste(card_img,(w_offset,h_offset))
                #print(i+1*j+1)
        #extra
        top_offset = int(padding/2)+((cols)*(c_height+padding))+int(c_height*small_factor)-(int((c_height+padding)*small_factor))
        for i in range(0,15):
            card_id = get_card(extra,i+1)
            if(card_id):
                card_img = Image.open(rel_path("db"+os.sep+card_id+".jpg"))
                card_img = card_img.resize((int(c_width*small_factor),int(c_height*small_factor)))
                img.paste(card_img,(int(padding/2)+(int((c_width+padding)*small_factor)*i),top_offset))

        top_offset = int(padding/2)+((cols)*(c_height+padding))+int(c_height*small_factor)
        for i in range(0,15):
            card_id = get_card(side,i+1)
            if(card_id):
                card_img = Image.open(rel_path("db"+os.sep+card_id+".jpg"))
                card_img = card_img.resize((int(c_width*small_factor),int(c_height*small_factor)))
                img.paste(card_img,(int(padding/2)+(int((c_width+padding)*small_factor)*i),top_offset))
        img.save(rel_path('deck_image.jpg'))
        #clean up
        for card_id in all_ids:
            if(os.path.isfile(rel_path("db"+os.sep+card_id+".jpg"))):
                os.remove(rel_path("db"+os.sep+card_id+".jpg"))
 
        return name,url,deck_name
    return False



class TTC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timer = Timer()
        self.timer_iteration = 0
        self.ctx = None
        with open(rel_path('bot_id.txt')) as t:
            self.bot_id = t.read()
        with open(rel_path('channel_id.txt')) as t:
            self.channel_id = t.read()

    async def query_with_timer(self,ttc_number):
        # query
        name,url,deck_name = scrape(ttc_number)
        if(not name):
            # if query fails, start timer unless it's been running more than 50 times
            if(self.timer_iteration < 60):
                self.timer_iteration += 1
                self.timer.start(300, self.query_with_timer,ttc_number)
            else:
                print(f"Failed to find the result of TTC {ttc_number}!")
        else:
            member = discord.utils.find(lambda m: m.name == name or m.display_name == name, self.ctx.guild.members)
            if(member):
                msg = f"{member.mention}"
            else:
                msg = f"{name}"
            msg += f" won TTC{ttc_number} with [{deck_name}](<{url}>)!"

            with open(rel_path("deck_image.jpg"),"rb") as f:
                pic = discord.File(f)
                channel = None
                try:
                    channel = self.bot.get_channel(int(self.channel_id))
                except:
                    await self.ctx.send("Channel not set! Sending here instead.")
                    await self.ctx.send(msg,file=pic)
                if(channel):
                    await channel.send(msg,file=pic)
            #send message
            #clean up files

    @commands.command(pass_context=True)
    async def set_channel(self, ctx):
        if(not ctx.message.author.id in admins):
            return
        with open(rel_path("channel_id.txt"), "w") as f:
            f.write(str(ctx.channel.id))
            self.channel_id = ctx.channel.id
        await ctx.send("Saved channel id!")

    @commands.command(pass_context=True)
    async def set_bot(self, ctx):
        if(not ctx.message.author.id in admins):
            return
        text = ctx.message.content
        if("<@" in text):
            user = (text[text.find("<@"):text.find(">")+1])
            print(user)
            if(user and len(user) > 3):
                user = user[2:-1]
                with open(rel_path("bot_id.txt"), "w") as f:
                    f.write(str(user)) 
                    self.bot_id = user
                await ctx.send(f"Saved <@{user}> as target bot!")

    
    @commands.Cog.listener()
    async def on_message(self,message):
        if(message.author.id != int(self.bot_id)):
            return

        self.ctx = await self.bot.get_context(message)
        text = message.content
        print(text)
        if(text.startswith("Congrats! The results of Toronto Time Capsule") and text.endswith("have been finalized.")):
            # extract number
            res = None
            for chunk in text.split(" "):
                try:
                    res = int(chunk.strip())
                except Exception as e:
                    pass
                    #print(e)
                if(res):
                    break
            if(res):
                # start timer
                self.timer_iteration = 0
                print(f"Found TTC number {res}")
                await self.query_with_timer(res)
       


async def setup(bot):
    await bot.add_cog(TTC(bot))
