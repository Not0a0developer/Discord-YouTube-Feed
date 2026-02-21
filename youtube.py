import asyncio
import aiohttp
import aiosqlite
from disnake import Webhook
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# Configuration
CHANNEL_IDS = {
    'Aqwav': 'UC0r0yb_GqHO5Ibv12vy905g', 
    'Unidoez': 'UCeScv-iQR6aj5Hb6J9dkSAg', 
    'UltrachiefGD': 'UCnlGCAfaWpjjSV-wCfYfF2w'
}
WEBHOOK_URL = "https://discord.com/api/webhooks/1474203933294727289/q22GrXKXNtMdGILiXa6rC6mQla6dsT7TB4BuKEyu5UD9NetdvQryeFEVemjWUoTUxULb"
UA = UserAgent(platforms='desktop')

async def init_db():
    async with aiosqlite.connect("youtube_uploads_posted.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS videos(title, link, name, published)")
        await db.commit()

async def post_to_discord(session, title, link, youtube_name, date):
    try:
        webhook = Webhook.from_url(WEBHOOK_URL, session=session)
        content = f"**New upload! {youtube_name}**\n*{title}*\n{link}\nDate: {date}"
        
        await webhook.send(
            content=content, 
            username="BSI Uploads", 
            avatar_url="https://i.imgur.com/22Q9QyJ.png"
        )
        print(f"Successfully posted: {title}")
    except Exception as e:
        print(f"Error posting to Discord: {e}")

async def channel_monitor():
    await init_db()
    
    # One session to rule them all (Better performance)
    async with aiohttp.ClientSession() as session:
        while True:
            for name, cid in CHANNEL_IDS.items():
                print(f"Checking {name}...")
                headers = {'User-Agent': UA.random}
                rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
                
                try:
                    async with session.get(rss_url, headers=headers) as response:
                        if response.status != 200:
                            print(f"Failed to fetch {name}: Status {response.status}")
                            continue
                            
                        xml_data = await response.text()
                        soup = BeautifulSoup(xml_data, "xml") # 'xml' is better for RSS feeds
                        entries = soup.find_all("entry")

                        async with aiosqlite.connect("youtube_uploads_posted.db") as db:
                            for entry in entries:
                                title = entry.title.text if entry.title else "No Title"
                                link = entry.link['href'] if entry.link else ""
                                author = entry.author.find("name").text if entry.author else name
                                pub_date = entry.published.text[:10] if entry.published else "2025-01-01"

                                # Check if already in DB
                                cursor = await db.execute("SELECT 1 FROM videos WHERE link = ?", (link,))
                                exists = await cursor.fetchone()
                                
                                if not exists:
                                    # Logic for filtering old videos
                                    if int(pub_date[:4]) >= 2025:
                                        await post_to_discord(session, title, link, author, pub_date)
                                        await asyncio.sleep(2) # Avoid Discord rate limits
                                    
                                    # Always add to DB so we don't check it again
                                    await db.execute("INSERT INTO videos VALUES (?, ?, ?, ?)", (title, link, author, pub_date))
                                    await db.commit()
                                    print(f"Added to DB: {title}")
                
                except Exception as e:
                    print(f"Error monitoring {name}: {e}")
                
                await asyncio.sleep(5) # Gap between different channel checks
            
            print("Finished cycle. Waiting 10 minutes...")
            await asyncio.sleep(600) # Wait 10 mins before checking all channels again

if __name__ == "__main__":
    try:
        asyncio.run(channel_monitor())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
