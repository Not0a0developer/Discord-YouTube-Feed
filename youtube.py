from disnake import Webhook
import aiohttp
import asyncio 
from bs4 import BeautifulSoup
import aiosqlite
from fake_useragent import UserAgent
## note: need to use `poetry shell` in order to access lxml

channel_ids = {'Aqwav': 'UC0r0yb_GqHO5Ibv12vy905g', 'Unidoez': 'UCeScv-iQR6aj5Hb6J9dkSAg', 'UltrachiefGD': 'UCnlGCAfaWpjjSV-wCfYfF2w'}  
# name of channel is not actually used in the script
# channel ID's can be found on desktop easily
# sometimes its in the url, e.g https://www.youtube.com/channel/UCqECaJ8Gagnn7YCbPEzWH6g - UCqECaJ8Gagnn7YCbPEzWH6g is the ID
# otherwise go to YouTube channel page, e.g https://www.youtube.com/@RecordingAcademy
# at the top you can see the channel description > click more > scroll down and click 'share channel' > click 'copy channel id'

# set list of user agents to use
ua = UserAgent(platforms='desktop')

async def create_webhook(title, link, youtube_name, date):
    async with aiohttp.ClientSession() as session:
        # url is the discord webhook url, this allows us to post
        discord_webhook_url = https://discord.com/api/webhooks/1474203933294727289/q22GrXKXNtMdGILiXa6rC6mQla6dsT7TB4BuKEyu5UD9NetdvQryeFEVemjWUoTUxULb
        webhook = Webhook.from_url(discord_webhook_url, session=session)

        # https://docs.disnake.dev/en/latest/api/webhooks.html#disnake.Webhook.send
        # username = name of webhook user
        ## await send(content=..., *, username=..., avatar_url=..., tts=False, ephemeral=..., suppress_embeds=..., flags=..., file=..., files=..., embed=..., embeds=..., allowed_mentions=..., view=..., components=..., thread=..., thread_name=..., applied_tags=..., wait=False, delete_after=..., poll=...)

        webhook_username = BSI Uploads # enter name of the Webhook user, can be anything (in this case, it's YouTube Bot)
        webhook_avatar = "https://i.imgur.com/22Q9QyJ.png" # enter a url to a pic if you want a avatar
        await webhook.send(content=f"New upload!  {youtube_name}!\n'{title}'\n{link}\n{date}", username=webhook_username, avatar_url=webhook_avatar)
        await asyncio.sleep(3)

        # connect to db
        db = await aiosqlite.connect("youtube_uploads_posted.db") # con obj

        cursor = await db.execute("""
            INSERT INTO videos VALUES
                (?, ?, ?, ?)""", (title, link, youtube_name, date))
        print("Added to DB", title, link)
        # changes need to be comitted before they enter the db
        await db.commit()
        await cursor.close()
        await db.close()


async def channel_monitor():
    while True:
        for chan_id in channel_ids:
            async with aiohttp.ClientSession() as session:
                HEADERS = {
                    'User-Agent': ua.random
                }
                await asyncio.sleep(18)
                async with session.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_ids[chan_id]}", headers=HEADERS) as r:
                    soup = BeautifulSoup(await r.text(), "lxml")  # grabs the entire html response

                    for entry in soup.find_all("entry"):
                        for title in entry.find_all("title"):
                            # title of video
                            title = title.text
                        for link in entry.find_all("link"):
                            # link to video
                            link = link["href"]
                        for name in entry.find_all("name"):
                            # name of YouTube user
                            youtube_name = name.text
                        for pub in entry.find_all("published"):
                            # date vid published
                            date = pub.text[:10]

                        # connect to db
                        db = await aiosqlite.connect("youtube_uploads_posted.db") # con obj
                        print("connected 1")
                        try:
                            cursor = await db.execute("CREATE TABLE videos(title, link, name, published)") # has no effect if already created
                            await db.commit()
                            await cursor.close()
                            print("exct")
                        except:
                            print("passed")
                            pass

                        # grab a list of tuples, that contains the names of all videos
                        cursor_check = await db.execute(f"SELECT * FROM videos WHERE title = ?", (title,))
                        db_grabbed = await cursor_check.fetchall()
                        print("fetched", db_grabbed)

                        # search db
                        if len(db_grabbed) > 0: # check if lst is empty, if not loop and check if matches vid name
                            print("Already in DB")
                            pass 
                            # we're already checking if the title is in the DB above, so no need to check again.
                        else:
                            print("Not in DB") # either DB is deleted and will be remade below, or entry isn't in DB

                            # when adding new channels, this avoids mass-posting of old videos:
                            if int(date[:4]) >= 2025:
                                post_vids = await create_webhook(title, link, youtube_name, date)
                            else:
                                # make sure old videos are added to db anyway
                                print(f"Adding old videos to DB: {title} - {date}")
                                cursor_old = await db.execute("""
                                    INSERT INTO videos VALUES
                                        (?, ?, ?, ?)""", (title, link, youtube_name, date))
                                await db.commit()
                                await cursor_old.close()
                        await cursor_check.close()  
                        await db.close()

        print("All videos posted!")
