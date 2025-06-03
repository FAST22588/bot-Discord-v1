# main.py

import discord
from discord.ext import commands
import gdown
import os
import asyncio
import time
from keep_alive import server_on

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1379036193525862460
LOG_CHANNEL_ID = 1378977947054247957
COUNTDOWN_TIME = 10

VIDEOS = {
    "กังฟูแพนด้า": "19p7U285U5KVkY-rHqq8QmApOzxdvc2aE",
    "ไอรอนแมน": "1tc4CwafrbcGHobe5WsVkuSX2jVqP9qxz",
    "เดดพูล": "1ru539tzbxOSe8vkQO677GsyeZBuOwW_a"
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==== เรียก Flask Server =====
server_on()

class DeliveryChoice(discord.ui.View):
    def __init__(self, file_name, title, ctx):
        super().__init__(timeout=60)
        self.file_name = file_name
        self.title = title
        self.ctx = ctx

    @discord.ui.button(label="📤 ส่งในกลุ่ม", style=discord.ButtonStyle.primary)
    async def send_to_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        video_channel = bot.get_channel(CHANNEL_ID)
        if video_channel:
            await video_channel.send(f"🎬 เรื่อง: **{self.title}**", file=discord.File(self.file_name))
        await self.log("กลุ่ม")
        await interaction.followup.send("✅ ส่งในกลุ่มเรียบร้อยแล้ว", ephemeral=True)
        self.cleanup()

    @discord.ui.button(label="📩 ส่งทาง DM", style=discord.ButtonStyle.secondary)
    async def send_to_dm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            await interaction.user.send(f"🎬 เรื่อง: **{self.title}**", file=discord.File(self.file_name))
            await self.log("DM")
            await interaction.followup.send("✅ ส่งทาง DM แล้ว!", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ ไม่สามารถส่ง DM ได้ (ผู้ใช้ปิดรับข้อความ)", ephemeral=True)
        self.cleanup()

    def cleanup(self):
        if os.path.exists(self.file_name):
            os.remove(self.file_name)
        self.stop()

    async def log(self, method):
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f"👀 **{self.ctx.author.display_name}** กำลังดูเรื่อง **{self.title}** ทาง {method}")

@bot.event
async def on_ready():
    print(f"✅ บอทออนไลน์: {bot.user}")

@bot.command()
async def ส่งคลิป(ctx, *, title: str = None):
    start_time = time.time()

    if not title:
        available_titles = " | ".join(VIDEOS.keys())
        await ctx.send(f"❗ กรุณาใส่ชื่อเรื่อง เช่น: `!ส่งคลิป กังฟูแพนด้า`\n📽 เรื่องที่มีให้: {available_titles}")
        return

    title = title.strip()

    if title not in VIDEOS:
        available_titles = " | ".join(VIDEOS.keys())
        await ctx.send(f"❌ ไม่พบชื่อเรื่อง: **{title}**\n📽 กรุณาเลือกจาก: {available_titles}")
        return

    msg = await ctx.send(f"⏳ กำลังเตรียมส่ง **{title}**...")

    file_id = VIDEOS[title]
    url = f"https://drive.google.com/uc?id={file_id}"
    FILE_NAME = "video.mp4"
    gdown.download(url, FILE_NAME, quiet=False)

    elapsed = time.time() - start_time
    remaining = max(0, int(COUNTDOWN_TIME - elapsed))

    for i in range(remaining, 0, -1):
        await msg.edit(content=f"⏳ กำลังส่ง **{title}** ใน {i} วินาที...")
        await asyncio.sleep(1)
    await msg.delete()

    await ctx.send(
        f"📌 ต้องการให้ส่งคลิป **{title}** ทางไหน?",
        view=DeliveryChoice(FILE_NAME, title, ctx)
    )

class MenuView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.used = False
        for title in VIDEOS.keys():
            self.add_item(MenuButton(title, ctx, self))

class MenuButton(discord.ui.Button):
    def __init__(self, title, ctx, view):
        super().__init__(label=title, style=discord.ButtonStyle.primary)
        self.title = title
        self.ctx = ctx
        self.parent_view = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ คุณไม่ได้เป็นคนเรียกเมนูนี้", ephemeral=True)
            return

        if self.parent_view.used:
            await interaction.response.send_message("⚠️ เลือกได้เพียง 1 ครั้ง หากต้องการเลือกใหม่ให้พิมพ์ `!เมนู` อีกครั้ง", ephemeral=True)
            return

        self.parent_view.used = True

        await interaction.response.defer()
        await self.ctx.invoke(self.ctx.bot.get_command("ส่งคลิป"), title=self.title)

        for child in self.parent_view.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        await interaction.message.edit(view=self.parent_view)
        self.parent_view.stop()

@bot.command()
async def เมนู(ctx):
    """แสดงรายการวิดีโอที่มีให้เลือก"""
    view = MenuView(ctx)
    await ctx.send("📋 กรุณาเลือกชื่อเรื่องที่ต้องการ:", view=view)

bot.run(TOKEN)
