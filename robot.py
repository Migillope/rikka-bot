"""
Discord Rikka Bot.
Carlos Saucedo, 2019
"""
import os
import discord
import string
import dbl
import json
import datetime
import asyncio
import sqlite3
import traceback
import sys
import time
import urllib
from urllib.parse import quote_plus
import Mods.gizoogle as gizoogle
from random import randint
from googletrans import Translator
import Mods.CleverApi as CleverApi
from time import sleep
import Mods.trivia as trivia
import Mods.triviaScore as triviaScore
from discord.emoji import Emoji
import Mods.EightBall as EightBall
import Mods.economy as econ
import Mods.beemovie as beemovie
import Mods.xkcd as xkcd
import Mods.wolfram as wolfram
import Mods.colors as colors
import Mods.assign as assign
import Mods.mal as mal
from pushbullet import Pushbullet

# Auth tokens
with open("json/config.json", "r") as h:
    config = json.load(h)
with open("json/indicators.json", "r") as h:
    indicators = json.load(h)

"""
Status message printing
"""
# Pushbullet error handling
pushbullet = Pushbullet(config["pushbulletapi"])

# Final variables
INFO = 0
WARN = 1
ERROR = 2


def statusMsg(message, category=0, push=False):
    timeStamp = datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S")
    if(category == 0):
        # Info
        status = "[INFO]"
    elif(category == 1):
        status = "[WARN]"
    elif(category == 2):
        status = "[ERROR]"
    if(push and config["pushbullet"]):
        pushbullet.push_note("rikka-bot", "str(status)" + " " + "str(message)")
    print(str(timeStamp) + ": " + str(status) + " " + str(message))


# Global Variables
startTime = time.time()

# Directory stuff
root_dir = os.path.dirname(__file__)

shardCount = 1  # Keeping it simple with 1 for now.

# lists
hug_relPath = "Lists/hug_gifs.list"
hug_absPath = os.path.join(root_dir, hug_relPath)
hugsfile = open(hug_absPath, "r")
huglist = hugsfile.read().splitlines()
hugCount = len(huglist)
hugsfile.close()

ramsay_relPath = "Lists/ramsay.list"
ramsay_absPath = os.path.join(root_dir, ramsay_relPath)
ramsayfile = open(ramsay_absPath)
ramsaylist = ramsayfile.read().splitlines()
ramsayCount = len(ramsaylist)
ramsayfile.close()

sfwinsult_relPath = "Lists/sfwinsults.list"
sfwinsult_absPath = os.path.join(root_dir, sfwinsult_relPath)
insultfile = open(sfwinsult_absPath)
insultlist = insultfile.read().splitlines()
insultCount = len(insultlist)
insultfile.close()


nsfwinsult_relPath = "Lists/nsfwinsults.list"
nsfwinsult_absPath = os.path.join(root_dir, nsfwinsult_relPath)
nsfwinsultfile = open(nsfwinsult_absPath)
nsfwinsultlist = nsfwinsultfile.read().splitlines()
nsfwInsultCount = len(nsfwinsultlist)
nsfwinsultfile.close()

# Cleverbot
if(config["cleverbot"]):
    try:
        statusMsg("Suspending CleverBot for now.", WARN)
        clever = CleverApi.Bot(config["userapi"], config["keyapi"])
    except:
        statusMsg("Failed to instantiate CleverBot.")

# Instances
client = discord.Client()
translator = Translator()
botlist = dbl.Client(client, config["bltoken"])
wolframClient = wolfram.Client(config["wolframapi"])

# Prefix things
defaultPrefix = ";"

# Trivia instantiation
question_relPath = "Lists/trivia_questions.list"
questionPath = os.path.join(root_dir, question_relPath)
answer_relPath = "Lists/trivia_answers.list"
answerPath = os.path.join(root_dir, answer_relPath)
trivia = trivia.triviaGame()
isSent = False

# Eight ball instantiation
eight = EightBall.eightBallGenerator()

# mal menus var
menus = {}


def getServerPrefix(guild):
    # Returns the server prefix.
    # If there is no server prefix set, it returns the defaultPrefix.
    guildID = str(guild.id)
    conn = sqlite3.connect("db/database.db")
    c = conn.cursor()

    c.execute("SELECT prefix FROM prefixes WHERE server=" + guildID)
    if(len(c.fetchall()) == 0):
        return defaultPrefix
    else:
        c.execute("SELECT prefix FROM prefixes WHERE server=" + guildID)
        return(c.fetchone()[0])


def command(string, message):
    """Builds a proper message prefix.

    Arguments:
        string {string} -- The command.
        message {string} -- The Discord `Message` object.

    Returns:
        string -- The prefix of the server along with the command.
    """
    serverPrefix = getServerPrefix(message.channel.guild)
    return (serverPrefix + string).lower()


def getArgument(command, message):
    """ Gets the argument of the command string, ignoring non-ASCII characters. """
    argument = message.content.replace(command + " ", "")
    argument = argument.encode("ascii", "ignore")
    return argument


def getRawArgument(command, message):
    """Fetches the raw argument of the command string, without being formatted."""
    argument = message.content.replace(command + " ", "")
    return argument


def fetchBooruPost(postID):
    try:
        with urllib.request.urlopen("".join(map(str, ("https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&id=", postID)))) as req:
            data = json.load(req)
        if len(data) > 0:
            post = data[0]
            embed = discord.Embed(color=0xff28fb)
            embed.set_image(url=post["file_url"])
            embed.title = "".join(
                map(str, ("Post ID:", post["id"], " | Created:", post["created_at"])))
            if post["source"] != "":
                embed.description = "\n".join(
                    (", ".join(post["tags"].split(" ")), post["source"]))
            else:
                embed.description = ", ".join(post["tags"].split(" "))
        else:
            embed = discord.Embed(
                color=0xff0000, title="Error", description="No posts were returned")
    except:
        embed = discord.Embed(color=0xff0000, title="Error",
                              description="Invalid post ID")
    return embed


def displayMA(id, embed):
    if id.startswith('a/'):
        data = mal.fetchAnime(id.lstrip('a/'))
    elif id.startswith('m/'):
        data = mal.fetchManga(id.lstrip('m/'))
    else:
        data = mal.fetchAnime(id)
        if int(data['request_status']) != 1:
            data = mal.fetchManga(id)
    embed.title = 'fuckin error m8'
    embed.description = 'get shat on'
    if data['request_status'] == 1:
        if 'title_formatted' in data:
            embed.title = data['title_formatted']
        if 'synopsis' in data:
            if len(data['synopsis']) > 600:
                short = data['synopsis'][0:599]
                embed.description = f'[[url]]({data["page_url"]})\n```\n{short}...\n```'
            else:
                embed.description = f'[[url]]({data["page_url"]})\n```\n{data["synopsis"]}\n```'
        if 'thumb_url' in data:
            embed.set_thumbnail(url=data['thumb_url'])
        if 'genres' in data:
            name = 'Genre'
            if len(data['genres']) > 1:
                name = 'Genres'
            embed.add_field(name=name, value=''.join(
                ('`', '`,`'.join(data['genres']), '`')), inline=False)
        if 'episodes' in data:
            embed.add_field(name='Episodes',
                            value=f'`{data["episodes"]}`', inline=True)
        if 'chapters' in data:
            embed.add_field(name='Chapters',
                            value=f'`{data["chapters"]}`', inline=True)
        if 'airing_status' in data:
            embed.add_field(name='Airing Status',
                            value=data["airing_status"], inline=True)
        if 'publishing_status' in data:
            embed.add_field(name='Publishing Status',
                            value=data["publishing_status"], inline=True)
        if 'origin' in data:
            embed.add_field(
                name='Origin', value=f'`{data["origin"]}`', inline=True)
        if 'licensors' in data:
            name = 'Licensor'
            if len(data['licensors']) > 1:
                name = 'Licensors'
            if data['licensors']:
                embed.add_field(name=name, value=''.join(
                    ('`', '`,`'.join(data['licensors']), '`')), inline=True)
        if 'studios' in data:
            name = 'Studio'
            if len(data['studios']) > 1:
                name = 'Studios'
            if data['studios']:
                embed.add_field(name=name, value=''.join(
                    ('`', '`,`'.join(data['studios']), '`')), inline=True)
        if 'authors' in data:
            name = 'Author'
            if len(data['authors']) > 1:
                name = 'Authors'
            if data['authors']:
                embed.add_field(name=name, value=''.join(
                    ('`', '`,`'.join(data['authors']), '`')), inline=True)
    elif data['request_status'] == 4:
        embed.title = 'Error!'
        embed.color = 0xff0000
        embed.description = 'Sorry, that can\'t be found!'
    else:
        embed.title = 'Fatal Error!'
        embed.color = 0xff0000
        embed.description = f'Sorry, there has been a serious error! (code `{data["request_status"]}`)'
    return embed


def canDelete(message):
    if message.author.id == client.user.id:
        return True
    guild = message.guild
    member = guild.get_member(client.user.id)
    permissions = message.channel.permissions_for(member)
    if permissions.manage_messages or message.author.id == config["admin"]:
        return True
    else:
        return False


@client.event
async def on_guild_join(guild):
    serversConnected = str(len(client.guilds))
    usersConnected = str(len(client.users))
    statusMsg("Joined server " + guild.name + "!")
    # Returns number of guilds connected to
    statusMsg("Guilds connected: " + serversConnected)
    statusMsg("Users connected: " + usersConnected)
    game = discord.Game(name='with ' + usersConnected +
                        ' users, on ' + serversConnected + ' servers!')
    await client.change_presence(activity=game)
    try:
        await botlist.post_server_count()
        statusMsg("Successfully published server count to dbl.")
    except:
        statusMsg("Failed to post server count to tbl.")


@client.event
async def on_guild_remove(guild):
    serversConnected = str(len(client.guilds))
    usersConnected = str(len(client.users))
    statusMsg("Left server " + guild.name + "!")
    # Returns number of guilds connected to
    statusMsg("Guilds connected: " + serversConnected)
    statusMsg("Users connected: " + usersConnected)
    game = discord.Game(name='with ' + usersConnected +
                        ' users, on ' + serversConnected + ' servers!')
    await client.change_presence(activity=game)
    try:
        await botlist.post_server_count()
        statusMsg("Successfully published server count to dbl.")
    except:
        statusMsg("Failed to post server count to tbl.")


@client.event
async def on_error(self, event_method, *args, **kwargs):
    if(config["pushbullet"]):
        print("Pushbullet is enabled.")
        statusMsg("Error.txt for details...", ERROR)
        print(file=sys.stderr)
        oldfile = open("error.txt", "r")
        f = open("error.txt", "w")
        f.write("===== ERROR SUMMARY =====\n")
        f.write("Timestamp: " +
                str(datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S")) + "\n")
        f.write("Exception in {}".format(event_method) + "\n")
        f.write("===== TRACEBACK =====\n")
        f.write(traceback.format_exc() + "\n\n")
        f.write(oldfile.read())
        f.close()
        oldfile.close()
        with open("error.txt", "r") as file:
            file_data = pushbullet.upload_file(file, str(
                datetime.datetime.now().strftime("%y_%m_%d_%H_%M_%S")) + "_error.txt")
        push = pushbullet.push_file(**file_data)
    else:
        print('Ignoring exception in {}'.format(event_method), file=sys.stderr)
        traceback.print_exc()


# @client.event
# async def on_raw_reaction_add(payload):
#     idMessage = str(payload.message_id)
#     idChannel = payload.channel_id
#     idUser = payload.user_id
#     emoji = payload.emoji.name
#     if str(idUser) == str(menus[idMessage]['user']):
#         if emoji in menus[idMessage]:
#             embed = discord.Embed(color=0x2e51a2)
#             channel = client.get_channel(idChannel)
#             await channel.send(embed=displayMA(str(menus.pop(idMessage)[emoji]), embed))
#             message = await channel.fetch_message(idMessage)
#             await message.delete()


# @client.event
# async def on_raw_message_delete(payload):
#     if payload.message_id in menus:
#         menus.pop(idMessage)


@client.event
async def on_message(message):
    """
    Universal commands
    """
    if message.author == client.user:
        # Makes sure bot does not reply to itself
        return

    elif message.author.bot == True:
        # Makes sure bot does not reply to another bot.
        return

    # making this bot less awful to add commands to
    prefix = getServerPrefix(message.channel.guild)
    cmd = message.content.lstrip(prefix).lower()
    rawArguments = cmd.lstrip(cmd.split(" ")[0]).lstrip(" ")
    spaceArguments = rawArguments.split(" ")
    commaArguments = rawArguments.split(",")

    if message.content.lower().startswith(command("sayd", message)):
        # Anonymous comment.
        arg = getRawArgument(command("sayd", message), message)
        arglist = arg.split()
        msg = ""
        for word in arglist:
            if "@everyone" in word:
                word = "everyone"
            if "@here" in word:
                word = "here"
            msg = msg + " " + word
        await message.channel.send(msg)
        await message.delete()

    elif str(message.channel).startswith("Direct Message"):
        # If message is direct message.
        msg = "Hi there! Here is my commands list. https://discordbots.org/bot/430482288053059584"
        await message.channel.send(msg)

    elif message.content.lower().startswith(command("help", message)):
        # Returns the README on the GitHub.
        msg = "{0.author.mention} https://discordbots.org/bot/430482288053059584".format(
            message)
        await message.channel.send(msg)

    elif message.content.lower() == command("hi", message) or message.content.lower() == command("hello", message):
        # Says hi and embeds a gif, mentioning the author of the message.
        msg = "h-hello {0.author.mention}-chan! ".format(
            message) + 'https://cdn.discordapp.com/attachments/402744318013603840/430592483282386974/image.gif'
        await message.channel.send(msg)

    elif message.content.lower().startswith(command("gizoogle", message)):
        # Gizoogles the given string and returns it.
        translatedMessage = gizoogle.text(
            getArgument(command("gizoogle", message), message))
        msg = "{0.author.mention} says: ".format(
            message) + translatedMessage.format(message)
        await message.channel.send(msg)
        await message.delete()

    elif message.content.lower().startswith(command("hugme", message)) or message.content.lower() == command("hug", message):
        # Hugs the author of the message.
        msg = "{0.author.mention}: ".format(
            message) + huglist[randint(0, hugCount - 1)]
        await message.channel.send(msg)

    elif message.content.lower().startswith(command("hug ", message)):
        # Hugs the first user mentioned by the author.
        msg = "{0.author.mention} hugs {0.mentions[0].mention}! ".format(
            message) + huglist[randint(0, hugCount - 1)]
        await message.channel.send(msg)
        await message.delete()

    elif message.content.lower().startswith(command("ramsay", message)):
        # Replies with a random Gordon Ramsay quote.
        msg = ramsaylist[randint(0, ramsayCount - 1)]
        await message.channel.send(msg)

    elif message.content.lower().startswith(command("gayy", message)):
        # no me
        msg = "no me {0.author.mention}".format(message)
        await message.channel.send(msg)

    elif message.content.lower().startswith(command("gay", message)):
        # no u
        msg = "no u {0.author.mention}".format(message)
        await message.channel.send(msg)

    elif message.content.lower().startswith(command("translate", message)):
        # Translates the given text into english.
        translatedMessage = translator.translate(
            getRawArgument(command("translate", message), message)).text
        msg = ("{0.author.mention}: translated text - " +
               translatedMessage).format(message)
        await message.channel.send(msg)

    elif message.content.lower().startswith(command("clever", message)):
        # Returns CleverBot's response.
        async with message.channel.typing():
            query = getRawArgument(command("clever", message), message)
            try:
                msg = clever.ask(query)
            except:
                msg = "cleverbot.io API error. Try again later."
            await message.channel.send(msg)

    elif message.content.lower().startswith(command("wolfram", message)):
        # Wolfram support.
        try:
            query = getRawArgument(command("wolfram", message), message)
            response = wolframClient.ask(query)
        except:
            # If no responses returned.
            response = "No results. Try revising your search."
        # Embed magic
        answerEmbed = discord.Embed(description=response, color=0xff8920)
        answerEmbed.set_author(name=query, icon_url="https://is5-ssl.mzstatic.com/image/thumb/Purple128/v4/19/fd/a8/19fda880-b15a-31a1-958d-32790c4ed5a4/WolframAlpha-AppIcon-0-1x_U007emarketing-0-0-GLES2_U002c0-512MB-sRGB-0-0-0-85-220-0-0-0-5.png/246x0w.jpg",
                               url=("https://m.wolframalpha.com/input/?i=" + quote_plus(query)))
        answerEmbed.set_footer(text="Wolfram|Alpha, all rights reserved")
        await message.channel.send(embed=answerEmbed)

    elif message.content.lower().startswith(command("info", message)):
        # Returns information about the bot.
        msg = ("Hi there! I'm Rikka. This robot was created by Leo. This server's command Prefix is: `" + getServerPrefix(
            message.channel.guild) + "`. To get help, use `" + getServerPrefix(message.channel.guild) + "help`.").format(message)
        if(message.author.id == config["admin"]):
            await message.channel.send("Hello, Leo! Thanks for creating me. ^-^")
        await message.channel.send(msg)

    elif (len(message.mentions) > 0) and (message.mentions[0] == client.user) and ("help" in message.content):
        # Returns information about the bot.
        msg = ("Hi there! I'm Rikka. This robot was created by Leo. This server's command Prefix is: `" + getServerPrefix(
            message.channel.guild) + "`. To get help, use `" + getServerPrefix(message.channel.guild) + "help`.").format(message)
        await message.channel.send(msg)

    elif message.content.lower().startswith(command("codeformat", message)):
        # Tells the user how to use discord's multiline code formatting
        msg = ("To use discord's muliline code formatting, send your message with the following template:\n"
            + "\`\`\`python\nprint(\"Hello, World\")\n\`\`\`\n\n"
            + "This outputs:\n```python\nprint(\"Hello, World\")\n```\n"
            + "Replace \"python\" with the language you are using to get some pretty syntax highlighting!")
        await message.channel.send(msg)
    
    elif message.content.lower().startswith(command("donate", message)) or message.content.startswith(command("patreon", message)):
        msg = (
            "Help my programmer out, become a patron today! https://www.patreon.com/LeoSaucedo")
        await message.channel.send(msg)

    elif message.content.lower().startswith(command("vote", message)):
        msg = "Vote for me to take over the world! https://discordbots.org/bot/430482288053059584/vote"
        await message.channel.send(msg)

    elif message.content.lower().startswith(command("insult ", message)):
        # Says a random insult using an insult generator
        if message.channel.is_nsfw():
            # If the channel is isfw.
            msg = "{0.author.mention} calls {0.mentions[0].mention} ".format(
                message) + nsfwinsultlist[randint(0, nsfwInsultCount - 1)] + "!"
        else:
            msg = "{0.author.mention} calls {0.mentions[0].mention} ".format(
                message) + insultlist[randint(0, insultCount - 1)] + "!"
        await message.channel.send(msg)
        await message.delete()

    elif message.content.lower().startswith(command("quickvote", message)):
        # Makes a new vote, and adds a yes and a no reaction option.
        voteText = getRawArgument(command("quickvote", message), message)
        voteEmbed = discord.Embed(color=0x0080c0, description=voteText)
        voteEmbed.set_author(
            name="New Vote by " + message.author.name + "!", icon_url=message.author.avatar_url)
        voteMsg = await message.channel.send(embed=voteEmbed)
        await voteMsg.add_reaction("👍")
        await voteMsg.add_reaction("👎")
        await message.delete()

    elif message.content.lower().startswith(command("rate", message)):
        # Rates a certain user or thing.
        thingToRate = getRawArgument(command("rate", message), message)
        rateScore = randint(0, 10)
        msg = ("I rate " + thingToRate + " a **" +
               str(rateScore) + "/10**.").format(message)
        await message.channel.send(msg)

    elif message.content.lower().startswith(command("suggest ", message)) or message.content.startswith(command("suggestion ", message)):
        # Adds ability to suggest new features.
        suggestion = getRawArgument(command("suggest", message), message)
        suggestionsFile = open("suggestions.txt", "a+")
        suggestionsFile.write(suggestion + "\n")
        msg = "{0.author.mention} Added your suggestion! It will be processed and may be added soon! Thanks for the help!".format(
            message)
        await message.channel.send(msg)

    elif message.content.lower() == command("beemovie", message):
        # Bee movie command.
        # TODO:: possible embed?
        quote = beemovie.getQuote()
        msg = quote.format(message)
        await message.channel.send(msg)

    elif message.content.lower().startswith(command("xkcd", message)):
        """
        XKCD Command.
        """
        if (message.content.lower() == command("xkcd random", message)) or (message.content.lower() == command("xkcd", message)):
            await message.channel.send(embed=xkcd.getRandomComic())

        elif message.content.lower() == command("xkcd latest", message):
            await message.channel.send(embed=xkcd.getLatestComic())

        else:
            comicID = int(getRawArgument(command("xkcd", message), message))
            image = xkcd.getComic(comicID)
            if image == None:
                msg = "{0.author.mention}, invalid comic ID!".format(message)
                await message.channel.send(msg)
            else:
                await message.channel.send(embed=image)

    # mal
    elif cmd.startswith('malqa'):
        await message.channel.send(embed=displayMA('a/' + str(mal.search(' ' + rawArguments, 'anime')[1][0][3]), discord.Embed(color=0x2e51a2)))
        if canDelete(message):
            await message.delete()
    elif cmd.startswith('malqm'):
        await message.channel.send(embed=displayMA('m/' + str(mal.search(' ' + rawArguments, 'manga')[1][0][3]), discord.Embed(color=0x2e51a2)))
        if canDelete(message):
            await message.delete()
    elif cmd.startswith("mal "):
        subcommand = rawArguments.split(" ")[0]
        embed = discord.Embed(color=0x2e51a2)
        if subcommand == "id":
            id = rawArguments.split(" ")[1].lower()
            await message.channel.send(embed=displayMA(id, embed))
            if canDelete(message):
                await message.delete()
        else:  # search
            rawString = ' ' + rawArguments
            searchType = 'anime'
            searchTypeLetter = 'a'
            rawString.replace('a/', '')
            if 'm/' in rawString.lower() or ' m ' in rawString.lower():
                searchType = 'manga'
                searchTypeLetter = 'm'
                rawString.replace('m/', '')
            data = mal.search(rawString, searchType)
            if data[0] == 1:
                if len(data[1]) > 1:
                    desc = ''
                    ref = {'user': str(message.author.id)}
                    r = len(data[1])
                    if r > 4:
                        r = 4
                    for i in range(0, r):
                        result = data[1][i]
                        desc = f'{desc}{indicators[i]} [{result[1]}][{result[0]}]\n'
                        ref[indicators[i]] = f'{searchTypeLetter}/{result[3]}'
                    embed.description = desc
                    sm = await message.channel.send(embed=embed)
                    menus[str(sm.id)] = ref
                    for i in range(0, r):
                        await sm.add_reaction(indicators[i])
                    await sm.delete(delay=30)
                    if canDelete(message):
                        await message.delete()
            elif data[0] != 1:
                if data[0] == 'NR':
                    embed.title = 'Error!'
                    embed.color = 0xff0000
                    embed.description = f'Sorry, there are no results for "{rawString}"! (code `ID` `10` `T`)'
                else:
                    embed.title = 'Fatal Error!'
                    embed.color = 0xff0000
                    embed.description = f'Sorry, there has been a serious error! (code `{data[0]}`)'
                await message.channel.send(embed=embed)

    elif message.content.lower().startswith(command("raffle", message)):
        nbusers = []
        for user in message.channel.guild.members:
            if not user.bot:
                nbusers.append(user)
        victim = nbusers[randint(0, len(nbusers))]
        await message.channel.send("".join((victim.mention, " Has been chosen!")))

    elif message.content.lower().startswith(command("latency", message)):
        await message.channel.send("Latency: " + str(int(client.latency * 1000)) + "ms")

    elif message.content.lower().startswith(command("uptime", message)):
        await message.channel.send("Uptime: " + str(time.time() - startTime))

    elif message.content.lower().startswith(command("give", message)):
        donorOriginalPoints = int(trivia.getScore(message.author.id))
        modPoints = getRawArgument(
            command("give", message), message).split(" ")[0]
        if (modPoints.isnumeric()):
            if (int(modPoints) > 0) and (int(donorOriginalPoints) >= int(modPoints)) and (len(message.mentions) == 1):
                trivia.subtractPoints(
                    message.channel.guild.id, message.author.id, int(modPoints))
                trivia.addPoints(message.channel.guild.id,
                                 message.mentions[0].id, int(modPoints))
                await message.channel.send("".join((message.author.mention, " has given ", message.mentions[0].mention, " ", modPoints, " points!")))
            elif int(modPoints) < 1:
                await message.channel.send("".join((message.author.mention, ", please enter a positive amount to give, thief!")))
            elif len(message.mentions) != 1:
                await message.channel.send("".join((message.author.mention, ", please mention 1 user to give your points to!")))
        else:
            await message.channel.send("".join((message.author.mention, ", \"", modPoints, "\" is not a valid number.")))

    elif message.content.lower().startswith(command("fight ", message)):
        numberOfPlayers = len(message.mentions)
        victorNumber = randint(0, numberOfPlayers)
        rewardAmount = randint(1, 5)
        authorLoses = False
        if (numberOfPlayers < 1) or (message.author in message.mentions):
            msg = "{0.author.mention}, you can't fight yourself! Choose a set of opponents.".format(
                message)
            await message.channel.send(msg)
        else:
            if victorNumber == numberOfPlayers:
                victor = message.author
            else:
                victor = message.mentions[victorNumber]
                if numberOfPlayers < 2:
                    trivia.subtractPoints(
                        message.guild.id, message.author.id, rewardAmount)
                    authorLoses = True
            # TODO: embed this and make it pretty.
            trivia.addPoints(message.guild.id, victor.id, rewardAmount)
            msg = ("{0.mention} wins! +"+str(rewardAmount) +
                   " points.").format(victor)
            await message.channel.send(msg)
            if authorLoses == True:
                msg = ("{0.author.mention}: For your loss, you lose " +
                       str(rewardAmount)+" points. Better luck next time!").format(message)
                await message.channel.send(msg)

    elif message.content.lower() == command("flip", message):
        """
        "Casino" Commands
        """
        # User is flipping a coin.
        coinResult = randint(0, 1)
        if coinResult == 0:
            msg = "{0.author.mention} flips a coin. It lands on heads.".format(
                message)
        elif coinResult == 1:
            msg = "{0.author.mention} flips a coin. It lands on tails.".format(
                message)
        await message.channel.send(msg)

    elif message.content.lower() == command("roll", message):
        # User rolls a die.
        diceResult = randint(1, 6)
        msg = ("{0.author.mention} rolls a die. It lands on " +
               str(diceResult) + ".").format(message)
        await message.channel.send(msg)

    elif message.content.lower().startswith(command("8ball", message)):
        result = eight.getAnswer()
        ballText = ("{0.author.mention}, " + result).format(message)
        ballEmbed = discord.Embed(color=0x8000ff)
        ballEmbed.set_author(
            name="Magic 8-Ball", icon_url="https://emojipedia-us.s3.amazonaws.com/thumbs/120/twitter/134/billiards_1f3b1.png")
        ballEmbed.add_field(name="Prediction:", value=ballText, inline=False)
        await message.channel.send(embed=ballEmbed)

    elif message.content.lower() == command("collect daily", message):
        """
        Economy commands.
        """
        userID = message.author.id
        serverID = message.guild.id
        if econ.hasCollectedToday(userID):
            msg = "{0.author.mention}, you have already collected today. Try again tomorrow!".format(
                message)
            await message.channel.send(msg)
        else:
            pointsToAdd = randint(1, 25)
            trivia.addPoints(serverID, userID, pointsToAdd)
            econ.setCollectionDate(userID)
            msg = "".join(map(str, (message.author.mention, ", you have gained ", pointsToAdd,
                                    " points! Your total points are now ", trivia.getScore(message.author.id), "!")))
            await message.channel.send(msg)

    elif message.content.lower() == command("leaderboard global", message):
        scoreList = ""
        globalScores = trivia.getGlobalLeaderboard()
        if len(globalScores) < 10:
            place = 1
            for score in globalScores:
                user = client.get_user(int(score[1]))
                if user != None:
                    score = score[2]
                    scoreList = scoreList + \
                        (str(place) + ": " + user.name +
                         " with "+str(score) + " points!\n")
                    place = place + 1
        else:
            i = 0
            place = 1
            while (place <= 10 and i < len(globalScores)):
                user = client.get_user(int(globalScores[i][1]))
                if user != None:
                    score = globalScores[i][2]
                    scoreList = scoreList + \
                        (str(place) + ": " + user.name +
                         " with "+str(score) + " points!\n")
                    place = place + 1
                i = i + 1

        scoreEmbed = discord.Embed(
            title="Global Leaderboard", color=0x107c02, description=scoreList)
        await message.channel.send(embed=scoreEmbed)

    elif message.content.lower() == command("leaderboard local", message):
        scoreList = ""
        localScores = trivia.getLocalLeaderboard(message.guild.id)
        if len(localScores) < 10:
            place = 1
            for score in localScores:
                user = client.get_user(int(score[1]))
                if user != None:
                    score = score[2]
                    scoreList = scoreList + \
                        ("".join((str(place), ": ", user.name,
                                  " with ", str(score), " points!\n")))
                    place = place + 1
        else:
            i = 0
            place = 1
            while (place <= 10 and i < len(localScores)):
                user = client.get_user(int(localScores[i][1]))
                if user != None:
                    score = localScores[i][2]
                    scoreList = scoreList + \
                        ("".join((str(place), ": ", user.name,
                                  " with ", str(score), " points!\n")))
                    place = place + 1
                i = i + 1
        scoreEmbed = discord.Embed(
            title="Local Leaderboard", color=0x107c02, description=scoreList)
        await message.channel.send(embed=scoreEmbed)

    elif message.content.lower() == command("trivia", message):
        """
        Trivia commands.
        """
        prefix = getServerPrefix(message.guild)
        msg = "To get a question, type " + prefix + "ask. To attempt an answer, type " + \
            prefix + "a (attempt). To reveal the answer, type " + \
            prefix + "reveal."
        await message.channel.send(msg)
        msg = "If you believe a question is unfair, type " + prefix + \
            "flag. It will be reviewed by our developers, and removed if appropriate."
        await message.channel.send(msg)
        msg = "To check your score, type " + prefix + "score. Good luck!"
        await message.channel.send(msg)

    elif message.content.lower().startswith(command("ask", message)):
        # Returns a randomly generated question.
        msg = trivia.getQuestion(message.guild.id)
        await message.channel.send(msg)
        global isSent
        trivia.setSent(message.guild.id, True)

    elif message.content.lower().startswith(command("reveal", message)):
        if trivia.getSent(message.guild.id) == True:
            msg = trivia.getAnswer(message.guild.id)
            await message.channel.send(msg)
            trivia.setSent(message.guild.id, False)
        elif trivia.getSent(message.guild.id) == False:
            msg = "You haven't asked a question yet!"
            await message.channel.send(msg)

    elif message.content.lower().startswith(command("flag", message)):
        trivia.flag()
        msg = "Flagged the question! Sorry about that."
        await message.channel.send(msg)

    elif message.content.lower() == (command("score", message)):
        msg = ("{0.author.mention}, your score is " +
               str(trivia.getScore(message.author.id))).format(message)
        await message.channel.send(msg)

    elif message.content.lower().startswith(command("score", message)) and len(message.mentions) > 0:
        msg = ("{0.mentions[0].mention}'s score is " +
               str(trivia.getScore(message.mentions[0].id))).format(message)
        await message.channel.send(msg)

    elif message.content.lower().startswith(command("a", message) + " "):
        # The user is attempting to answer the question.
        attempt = getRawArgument(command("a", message), message)
        if trivia.getSent(message.guild.id) == True:
            # If the question is sent and the answer has not yet been revealed.
            if trivia.format(attempt) == trivia.format(trivia.getAnswer(message.guild.id)):
                # If the answer is correct.
                reward = randint(1, 20)
                msg = ("{0.author.mention}, correct! The answer is " + trivia.getAnswer(
                    message.guild.id)+". +" + str(reward) + " points!").format(message)
                await message.channel.send(msg)
                trivia.addPoints(message.guild.id, message.author.id, reward)
                trivia.setSent(message.guild.id, False)
        else:
            msg = "You haven't gotten a question yet!"
            await message.channel.send(msg)

    elif message.content.lower().startswith(command("board", message)):
        """
        Board enable command.
        """
        if message.channel.permissions_for(message.author).manage_channels == True or message.author.id == config["admin"]:
            if getRawArgument(command("board", message), message) == "enable":
                if message.channel.permissions_for(message.author).manage_channels == True or message.author.id == config["admin"]:
                    await message.guild.create_text_channel('board')
                    msg = "Created board channel! You might want to change the channel permissions/category."
                    await message.channel.send(msg)
                else:
                    msg = "Insufficient permissions."
                    await message.channel.send(msg)

    elif message.content.lower().startswith(command("kick", message)):
        """
        Kick command.
        """
        if message.channel.permissions_for(message.author).kick_members == True or message.author.id == config["admin"]:
            user = message.mentions[0]
            try:
                await message.guild.kick(user)
                msg = "Kicked " + user.name + "!"
                await message.channel.send(msg)
            except:
                msg = "Failed to kick user."
                await message.channel.send(msg)
        else:
            msg = "Insufficient permissions."
            await message.channel.send(msg)

    elif message.content.lower().startswith(command("ban", message)):
        """
        Ban command.
        """
        if message.channel.permissions_for(message.author).ban_members == True or message.author.id == config["admin"]:
            user = message.mentions[0]
            try:
                await message.guild.ban(user)
                msg = "Banned " + user.name + "!"
                await message.channel.send(msg)
            except:
                msg = "Failed to ban user."
                await message.channel.send(msg)

        else:
            msg = "Insufficient permissions."
            await message.channel.send(msg)

    elif message.channel.permissions_for(message.author).manage_messages == True or message.author.id == config["admin"]:
        """
        Moderator commands.
        """
        if message.content.lower().startswith(command("clear", message)):
            # Clears a specified number of messages.

            if(len(message.mentions) > 0):
                # Clear command contains a mention.
                number = 0
                messages = []
                async for msg in message.channel.history():
                    if msg.author == message.mentions[0]:
                        messages.append(msg)
                        number = number+1
                if(len(messages) < 1):
                    msg = "Could not find any messages from the specified user."
                    await message.channel.send(msg)
                else:
                    await message.channel.delete_messages(messages)
                    msg = "deleted " + str(number) + " messages!"
                    deletemsg = await message.channel.send(msg)
                    sleep(5)
                    await deletemsg.delete()

            else:
                number = int(getArgument(command("clear", message), message))
                await message.channel.purge(limit=(number + 1), bulk=True)
                msg = "deleted " + str(number) + " messages!"
                deletemsg = await message.channel.send(msg)
                sleep(5)
                await deletemsg.delete()

        elif message.content.lower().startswith(command("mute", message)):
            if len(message.mentions) > 0:
                sinner = message.mentions[0]
                await message.channel.set_permissions(sinner, send_messages=False)
                msg = "Muted {0.mentions[0].mention}!".format(message)
                await message.channel.send(msg)
            else:
                msg = "You must specify a user."
                await message.channel.send(msg)

        elif message.content.lower().startswith(command("unmute", message)):
            if len(message.mentions) > 0:
                sinner = message.mentions[0]
                await message.channel.set_permissions(sinner, send_messages=True)
                msg = "Unmuted {0.mentions[0].mention}!".format(message)
                await message.channel.send(msg)
            else:
                msg = "You must specify a user."
                await message.channel.send(msg)

    if message.channel.permissions_for(message.author).administrator == True or message.author.id == config["admin"]:
        """
        Administrator Commands.
        """
        if message.content.lower().startswith(command("prefix", message)):
            newPrefix = getRawArgument(command("prefix", message), message)
            oldPrefix = getServerPrefix(message.channel.guild)
            if(newPrefix == oldPrefix + "prefix"):
                msg1 = "Invalid prefix. Try again."
                msg2 = "Usage: `" + oldPrefix + "prefix (prefix)`"
                await message.channel.send(msg1)
                await message.channel.send(msg2)
            else:
                conn = sqlite3.connect("db/database.db")
                c = conn.cursor()
                c.execute("SELECT * FROM prefixes WHERE server='" +
                          str(message.channel.guild.id) + "';")
                msg = ""
                if(len(c.fetchall()) == 0):
                    # If the entry does not exist
                    t = (str(message.channel.guild.id), str(newPrefix))
                    c.execute('INSERT INTO prefixes VALUES (?, ?);', t)
                    msg = ("Set server prefix to `" +
                           newPrefix + "` !").format(message)
                else:
                    t = (str(newPrefix), str(message.channel.guild.id))
                    c.execute('''
                    UPDATE prefixes
                    SET prefix=?
                    WHERE server=?;
                    ''', t)
                    msg = ("Changed server prefix to `" +
                           newPrefix + "` !").format(message)
                conn.commit()
                conn.close()
                await message.channel.send(msg)

        if (message.author.id != 400360503622369291) and (message.channel.guild.id == 401480405561114624):
            if message.content.lower().startswith(command("add", message)):
                points = getRawArgument(
                    command("add", message), message).split(" ")[0]
                victors = message.mentions
                mentions = []
                for victor in victors:
                    trivia.addPoints(message.channel.guild.id,
                                     victor.id, int(points))
                    mentions.append(victor.mention)
                await message.channel.send("".join(("Added ", points, " points to ", (", ".join(mentions)), "!")))

            elif message.content.lower().startswith(command("subtract", message)):
                points = getRawArgument(
                    command("subtract", message), message).split(" ")[0]
                victims = message.mentions
                mentions = []
                for victim in victims:
                    trivia.subtractPoints(
                        message.channel.guild.id, victim.id, int(points))
                    mentions.append(victim.mention)
                await message.channel.send("".join(("Took ", points, " points from ", (", ".join(mentions)), "!")))

    """
    Color Roles
    """
    if (message.content.startswith(command("color ", message)) and not colors.getColorMode(message.channel.guild.id)):
        msg = "{0.author.mention}, color roles are not enabled for this server... sorry!".format(
            message)
        await message.channel.send(msg)
    if ((message.channel.permissions_for(message.author).manage_roles == True or message.author.id == config["admin"])
            and message.content.lower().startswith(command("colors", message))):
        status = getRawArgument(command("colors", message), message)
        if(status == "enable"):
            # Enable colors.
            colors.setColorMode(True, message.channel.guild.id)
            await message.channel.send("Enabled custom user colors!")
        elif(status == "disable"):
            # Disable colors.
            colors.setColorMode(False, message.channel.guild.id)
            await message.channel.send("Disabled custom user colors.")
        else:
            msg = "{0.author.mention}, please enter a valid command.".format(
                message)
            await message.channel.send(msg)
    elif (message.content.lower() == command("color ", message) + "reset"):
        # Resets all color roles.
        for role in message.author.roles:
            if(role.name.startswith("Color - ")):
                await message.author.remove_roles(role)
                msg = "{0.author.mention}, removed your color roles!".format(
                    message)
                await message.channel.send(msg)
    elif (message.content.lower().startswith(command("color ", message))
            and colors.getColorMode(message.channel.guild.id)):
        # If colors are enabled
        colorName = getRawArgument(command("color", message), message)
        # e.g. "blue"
        color = colors.getColor(colorName)
        if(color == None):
            msg = "{0.author.mention}, please enter a valid color.".format(
                message)
            await message.channel.send(msg)
        else:
            # Returns a color object.
            roleCreated = False
            # Removing any previously added roles.
            for role in message.author.roles:
                if(role.name.startswith("Color - ")):
                    await message.author.remove_roles(role)
            # Searching to see if the color role is already in the server.
            for role in message.channel.guild.roles:
                if(role.name == ("Color - " + colorName)):
                    roleCreated = True
                    await role.edit(position=(message.channel.guild.me.top_role.position-1))
                    await message.author.add_roles(role)
            if(not roleCreated):
                # If the role has not yet been created.
                # Remove the previously existing role - if applicable.
                # Create a new role with the specified color.
                newRole = await message.channel.guild.create_role(color=color, name=("Color - " + colorName))
                await message.channel.send(newRole)
                # Place the role directly under the bot's top role position.
                await newRole.edit(position=(message.channel.guild.me.top_role.position-1))
                await message.author.add_roles(newRole)

            msg = ("{0.author.mention}, changed your color to " +
                   colorName + "!").format(message)
            await message.channel.send(msg)

    """
    Self-Assignable Roles
    """
    if message.content.lower().startswith(command("iamlist", message)):
        # List the enabled roles for the server
        assignList = ""
        assignableRoles = assign.getAssignList(message.guild.id)
        if len(assignableRoles) > 0:
            for role in assignableRoles:
                # If the role still exists,
                # Add it to the list of assignable roles.
                roleObject = discord.utils.get(
                    message.guild.roles, id=int(role[0]))
                if roleObject != None:
                    # If the role still exists in the serer,
                    # Add it to the print list.
                    roleName = roleObject.name
                    assignList += roleName+"\n"
                else:
                    # If the role doesn't exist anymore,
                    # delete it from the database.
                    assign.setAssign(message.channel.guild.id, int(role[0]), False)
            if(assignList != ""):
                assignEmbed = discord.Embed(
                    title="Assignable Roles", color=0x4287f5, description=assignList)
                await message.channel.send(embed=assignEmbed)
            else:
                msg = "{0.author.mention}, no assignable roles have been set.".format(
                message)
                await message.channel.send(msg)
        else:
            msg = "{0.author.mention}, no assignable roles have been set.".format(
                message)
            await message.channel.send(msg)
    elif message.content.lower().startswith(command("assign enable", message)) or message.content.lower().startswith(command("assign disable", message)):
        # Enable assignability.
        if(message.channel.permissions_for(message.author).manage_roles == True or message.author.id == config["admin"]):
            # User has permission.
            enabling = None
            if message.content.lower().startswith(command("assign enable", message)):
                # User is attempting to enable the role.
                roleName = getRawArgument(
                    command("assign enable", message), message)
                enabling = True
            elif message.content.lower().startswith(command("assign disable", message)):
                # User is attempting to disable the role.
                roleName = getRawArgument(
                    command("assign disable", message), message)
                enabling = False
            # If the role has already been created.
            role = discord.utils.get(message.guild.roles, name=(roleName))
            if(role == None and enabling):
                # If the role has not been created.
                # Create a new role.
                role = await message.channel.guild.create_role(name=str(roleName))
                roleId = role.id
            if role != None:
                # Role has been created.
                roleId = role.id
                assign.setAssign(message.channel.guild.id, roleId, enabling)
                if(enabling):
                    msg = ("Enabled role `" + roleName +
                           "` assignment!").format(message)
                    await message.channel.send(msg)
                else:
                    msg = ("Disabled role `" + roleName +
                           "` assignment.").format(message)
                    await message.channel.send(msg)
        else:
            msg = "{0.author.mention}, you must have `Manage Roles` permission to enable/disable role assignment.".format(
                message)
            await message.channel.send(msg)
    elif message.content.lower().startswith(command("iam", message)) or message.content.lower().startswith(command("iamnot", message)):
        # Assign and de-assign roles.
        assigning = None
        if(message.content.lower().startswith(command("iamnot", message))):
            roleName = getRawArgument(command("iamnot", message), message)
            assigning = False
        else:
            roleName = getRawArgument(command("iam", message), message)
            assigning = True
        # Check to see if role exists.
        role = discord.utils.get(message.guild.roles, name=roleName)
        if(role == None):
            # If role does not exist
            msg = "{0.author.mention}, that role does not exist!".format(
                message)
            await message.channel.send(msg)
        else:
            # Role exists
            roleId = role.id
            if(assign.isAssignable(roleId)):
                # If the role is assignable.
                roleAssigned = None
                if(discord.utils.get(message.author.roles, id=roleId) != None):
                    # Role is not already assigned.
                    roleAssigned = True
                else:
                    roleAssigned = False
                if(assigning and roleAssigned):
                    msg = "{0.author.mention}, that role is already assigned to you!".format(
                        message)
                    await message.channel.send(msg)
                elif(not assigning and not roleAssigned):
                    msg = "{0.author.mention}, you don't have that role assigned!".format(
                        message)
                    await message.channel.send(msg)
                elif(assigning and not roleAssigned):
                    await message.author.add_roles(role)
                    msg = ("{0.author.mention}, role `" + roleName +
                           "` has been assigned.").format(message)
                    await message.channel.send(msg)
                elif(not assigning and roleAssigned):
                    await message.author.remove_roles(role)
                    msg = ("{0.author.mention}, removed role `" +
                           roleName + "`.").format(message)
                    await message.channel.send(msg)

            else:
                msg = "{0.author.mention}, that role is not assignable!".format(
                    message)
                await message.channel.send(msg)

    """
    the lewd
    """
    if message.content.lower().startswith(command("gelbooru", message)):
        if message.channel.is_nsfw() == True:
            cmd = message.content.lstrip(command("gelbooru", message))
            args = cmd.lstrip(cmd.split(" ")[0]).lstrip(" ")
            with urllib.request.urlopen("https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1") as req:
                data = json.load(req)
            embed = discord.Embed(color=0xff0000, title="Error",
                                  description="baaka, you need to specify a subcommand. desu.")
            if args == "random":
                post = data[randint(0, len(data)-1)]["id"]
                embed = fetchBooruPost(post)
            if args == "latest":
                post = data[0]["id"]
                embed = fetchBooruPost(post)
            if args.startswith("tags"):
                tags = args.split(" ")[1].split(",")
                try:
                    with urllib.request.urlopen("".join(("https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&tags=", "+".join(map(str, tags))))) as req:
                        data = json.load(req)
                    post = data[randint(0, len(data)-1)]["id"]
                    embed = fetchBooruPost(post)
                except Exception as e:
                    statusMsg(e, 2)
                    embed = discord.Embed(
                        color=0xff0000, title="Error", description=str(e))
            if args.startswith("id"):
                id = args.split(" ")[1]
                if int(id) <= data[0]["id"] and int(id) > 0:
                    embed = fetchBooruPost(id)
                else:
                    embed = discord.Embed(
                        color=0xff0000, title="Error", description="Invalid post ID")
            await message.channel.send(embed=embed)
        else:
            await message.channel.send("This command requires the channel to be NSFW.")

    """
    Misc gif commands.
    """
    if message.content.lower() == command("shocked", message):
        msg = "https://cdn.discordapp.com/attachments/402744318013603840/430591612637413389/image.gif"
        await message.channel.send(msg)
    elif message.content.lower() == command("smile", message):
        msg = "https://cdn.discordapp.com/attachments/402744318013603840/430591877834735617/image.gif"
        await message.channel.send(msg)
    elif message.content.lower() == command("hentai", message):
        msg = "https://cdn.discordapp.com/attachments/402744318013603840/430593080215994370/image.gif"
        await message.channel.send(msg)
    elif message.content.lower() == command("blush", message):
        msg = "https://cdn.discordapp.com/attachments/402744318013603840/430593551554969600/image.gif"
        await message.channel.send(msg)
    elif message.content.lower() == command("bdsm", message):
        msg = "http://i.imgur.com/dI4zJwk.gif"
        await message.channel.send(msg)
    elif message.content.lower() == command("rekt", message):
        msg = "https://cdn.discordapp.com/attachments/402744318013603840/430594037427470336/image.gif"
        await message.channel.send(msg)
    elif message.content.lower() == command("boop", message):
        msg = "https://cdn.discordapp.com/attachments/402744318013603840/430594711602987008/image.gif"
        await message.channel.send(msg)
    elif message.content.lower() == command("fuckoff", message):
        msg = "https://cdn.discordapp.com/attachments/402744318013603840/430594846022041601/image.gif"
        await message.channel.send(msg)
    elif message.content.lower() == command("sanic", message):
        msg = "https://cdn.discordapp.com/attachments/402744318013603840/430595068156575756/image.gif"
        await message.channel.send(msg)
    elif message.content.lower() == command("dreamy", message):
        msg = "https://cdn.discordapp.com/attachments/402744318013603840/430595392669745153/image.gif"
        await message.channel.send(msg)
    elif message.content.lower() == command("waifu", message):
        msg = "https://i.pinimg.com/originals/bd/9a/a4/bd9aa46572e180ec6df08119429a1e81.jpg"
        await message.channel.send(msg)
    elif message.content.lower() == command("trash", message):
        msg = "https://media1.tenor.com/images/29307201260fb755e7ff9fec21f22c95/tenor.gif?itemid=8811727"
        await message.channel.send(msg)
    elif message.content.lower() == command("kys", message):
        msg = "https://imgur.com/YfYwzcN"
        await message.channel.send(msg)
    elif message.content.lower() == command("ping", message):
        msg = "Why did you feel the need to ping everyone? What could possibly be so important that you decided to alert everyone on this god-forsaken server to what you had to say? Did you get a girlfriend? Lose your virginity? Did you become president of the goddamn world? Is that why you had to ping us? I bet you're so proud of yourself, snickering to yourself as you watch the chaos unfold after your ping. You think you're so funny, interrupting everyone's day with your asinine messages. But guess what, you're pathetic. The only way you were able to get someone's attention is by shoving down your sad excuse of a thought down everyone's throat, shattering their focus with that loud PING! I wonder how many people you've killed by doing this. Maybe someone was driving and the ping caused them to lose control and crash. Maybe a surgeon was performing open heart surgery and was jolted by the obnoxious pinging noise of a new notification. Can you live with yourself knowing how many lives you've cost by thinking you had something important to say? I hope you're happy with yourself."
        await message.channel.send(msg)

"""
Bot login actions
"""
@client.event
async def on_ready():
    if(config["pushbullet"]):
        pushbullet.push_note(
            "Rikka-bot Startup", str(datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S")))
    statusMsg("Logged in as")
    statusMsg(client.user.name)
    statusMsg(client.user.id)
    statusMsg("-------")
    statusMsg("loaded hugs: " + str(hugCount))
    statusMsg("loaded Ramsay quotes: " + str(ramsayCount))
    statusMsg("Loaded questions: " + str(trivia.getQuestionCount()))
    serversConnected = len(client.guilds)
    usersConnected = len(client.users)
    # Returns number of guilds connected to
    statusMsg("Guilds connected: " + str(serversConnected))
    statusMsg("Shards connected: " + str(shardCount))
    statusMsg("Users connected: " + str(usersConnected))
    game = discord.Game(name='with ' + str(usersConnected) +
                        ' users, on '+str(serversConnected)+" servers!")
    await client.change_presence(activity=game)
    try:
        await botlist.post_server_count()
        statusMsg("Successfully published server count to dbl.")
    except Exception as e:
        print(e)
        statusMsg("Failed to post server count to dbl.")

while True:
    client.run(config["token"])  # runs the bot.
    startTime = time.time()
