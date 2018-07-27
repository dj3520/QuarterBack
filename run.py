import time
starttime = time.time()

import discord
from discord import opus

import asyncio, sys, math, datetime
from libs import savesys, ACIF2, utils

import auth

import logging
log = logging.getLogger()
format = logging.Formatter(fmt="%(asctime)s [%(levelname)s] [%(name)s.%(funcName)s:%(lineno)d] %(message)s", datefmt="%m/%d/%Y %H:%M:%S")

import logging.handlers
handler = logging.handlers.RotatingFileHandler("quarterback.log", backupCount=2, encoding="utf-8", mode="w")

# handler = logging.FileHandler(filename="roboquarter.log", encoding="utf-8", mode="w")
handler.setFormatter(format)
log.addHandler(handler)

con = logging.StreamHandler(sys.stdout)
con.setFormatter(format)
log.addHandler(con)

log.setLevel(10)

log.info("Starting QuarterBack..")
log.info("Python: "+sys.version)
log.info("Discord: "+discord.__version__)

log.debug("Logging level = {}".format(log.getEffectiveLevel()))

for l in ['discord.client', 'discord.gateway', 'discord.http', 'libs.ACIF2', 'websockets']: # , 'libs.twitch']: #, 'libs.savesys']:
  o = logging.getLogger(l)
  o.setLevel(logging.INFO)
  o.debug('Set '+l+' level to INFO')

custom_loop = asyncio.get_event_loop()

settings = savesys.SaveSys("qb-vars.json")
startingUpDiscord = True

## === ~~~ -- Routines -- ~~~ === ##

async def get_guild_setting(ugid, key, default=None):
  gid = str(ugid)
  guild_settings = settings.readSavedVar("guilds", default={})
  if not guild_settings == {}:
    if gid in guild_settings.keys():
      if key in guild_settings[gid].keys():
        return guild_settings[gid][key]
      return default
  old_guild_settings = settings.readSavedVar("guild-"+str(gid), default={})
  if old_guild_settings == {}: return default
  guild_settings[gid] = old_guild_settings
  settings.setSavedVar("guilds", guild_settings)
  settings.delSavedVar("guild-"+str(gid))

async def set_guild_setting(ugid, key, val):
  gid = str(ugid)
  guild_settings = settings.readSavedVar("guilds", default={})
  if not guild_settings == {}:
    if gid in guild_settings:
      guild_settings[gid][key] = val
      settings.setSavedVar("guilds", guild_settings)
      return True

  old_guild_settings = settings.readSavedVar("guild-"+str(gid), default={})
  guild_settings[gid] = old_guild_settings
  guild_settings[gid][key] = val
  settings.setSavedVar("guilds", guild_settings)
  settings.delSavedVar("guild-"+str(gid))

def iterate_users_as_members():
  user_members = []
  for m in quarter.get_all_members():
    if not m.id in user_members:
      user_members.append(m.id)
      yield m

async def get_user_as_member(user):
  for m in quarter.get_all_members():
    if user.id == m.id: return m

async def send2owner(this):
  await write_message(appinf.owner, this)

async def failed_reaction(message):
  logging.info('Failed to add reaction.')
  if utils.is_pm(message.channel): return
  channel_settings = await get_guild_setting(message.guild.id, "channel-"+str(message.channel.id), default={})
  if not "AskedForReactPerms" in channel_settings.keys():
    channel_settings["AskedForReactPerms"] = True
    await set_guild_setting(message.guild.id, "channel-"+str(message.channel.id), channel_settings)
  elif channel_settings["AskedForReactPerms"]:
    logging.debug("Already asked up for "+str(message.channel.id))
    return
  await write_message(message.guild.owner, "I do not have `Add Reactions` permission in `"+message.guild.name+"/"+message.channel.name+"`")

async def failed_message(where, want_perm):
  logging.info('Failed to send message.')
  if utils.is_pm(where): return
  channel_settings = await get_guild_setting(where.guild.id, "channel-"+str(where.id), default={})
  key = "AskedFor"+want_perm
  if not key in channel_settings.keys():
    channel_settings[key] = True
    await set_guild_setting(where.guild.id, "channel-"+str(where.id), channel_settings)
  elif channel_settings[key]:
    logging.debug("Already asked for "+key+" in "+str(where.id))
    return
  await write_message(where.guild.owner, "I do not have `"+want_perm+"` permission in `"+where.guild.name+"/"+where.name+"`")

async def write_message(where, content, tts=False):
  isEmbed = isinstance(content, discord.embeds.Embed)

  if isinstance(where, list):
    out = {}
    for i in where:
      await asyncio.sleep(0)
      out[i] = await write_message(i, content, wait=wait, tts=tts)
    return out

  if where == None:
    log.warning("Tried to send a message without a destination!")
    return

  if not isEmbed:
    if content == None: return False
    blockquote = '```' in content

    if len(content) > 2000:
      await write_message(where, "My reply was too long. (More than 2000 characters)", wait=False)

    try:
      sent = await where.send(content, tts=tts)
      return sent
    except discord.errors.Forbidden:
      want_perm = "Send Message"
      if tts == True:
        want_perm = "Send TTS Message"
        await write_message(where, content, wait=wait, tts=False)
      await failed_message(where, want_perm)
      return None

  try:
    # Thank the guys at Discord API/python_discord-py
    # log.log(5, dir(where))
    sent = await where.send(None, embed=content)
    return sent
  except discord.Forbidden:
    want_perm = "Embed Links"
    await failed_message(where, want_perm)
    return None

async def shutdown(dclient, message):
  await write_message(message.channel, "Goodbye.")
  await dclient.logout()

### === ~~~ -- DISCORD CLASS -- ~~~ === ###

class discord_side(discord.Client):
  async def on_connect(self):
    log.debug("Client connection to discord SUCCESS")

  async def on_resume(self):
    log.debug("Session resumed.")

  async def on_error(self, event, *args, **kwargs):
    e = sys.exc_info()[0]
    log.exception(e)

    if hasattr(e, 'message'): e = e.message
    await send2owner("Errors occured in "+str(event)+"()\n"+str(args)+"\n"+str(kwargs)+"\n"+str(e))

    if not len(args) == 0:
      if type(args[0]) == discord.Message:
        await send2owner("["+args[0].author.name+"]: "+args[0].content)

  async def on_ready(self):
    # Avoid running again after a re-connect
    global startingUpDiscord

    if not startingUpDiscord:
      log.debug("Noticed a reconnect.")
      return

    startingUpDiscord = False

    global appinf
    appinf = await quarter.application_info()
    global ready_time
    ready_time = time.time()
    startedtime = math.trunc((ready_time - starttime) * 100) / 100
    logging.info("Started in "+str(startedtime)+" seconds.")
    logging.info(40*"=")

  async def on_member_join(self, member):
    log.info("{} joined the {} server".format(member.name, member.guild.name))

  async def on_guild_join(self, guild):
    log.info(guild.name+" joined!")
    await send2owner(guild.name+" joined!")

  async def on_message(self, message):
    admin = message.author.id == appinf.owner.id and (quarter.user in message.mentions or utils.is_pm(message.channel))
    requested = message.content.startswith("qb ")

    if not admin and not requested: return
    if message.author == self.user: return

    check = ACIF2.command_matcher()
    if admin:
      cleaned = utils.remove_activation_text(message, sendback=True)
      mentions = cleaned[1]
      cleaned = cleaned[0]
      check.add("sudo reboot", shutdown(self, message))
      check.add("list admin commands", "sudo reboot")
    elif requested:
      cleaned = message.content.replace("qb ", "")
      check.add("ping", "Pong!")

    do = check.match(cleaned.lower())
    if isinstance(do, str):
      await write_message(message.channel, do)
      return
    elif not do == None:
      await do
      return

## === ~~~ -- Commands -- ~~~ === ##

quarter = discord_side()
keep_going = True
try:
  custom_loop.run_until_complete(quarter.login(auth.discord_token))
except discord.LoginFailure:
  log.critical("Cannot start! Login failure! Check token.")
  keep_going = False

if keep_going:

  try:
    custom_loop.run_until_complete(quarter.connect())
  except KeyboardInterrupt:
    log.warning("KeyboardInterrupt!")
  except discord.GatewayNotFound:
    log.warning("Websocket connection failed. Discord might be down!")
  finally:
    pass # custom_loop.run_until_complete(do_shutdown_prep())

  if not quarter.is_closed():
    log.warning("Loop stopped but DISCORD still logged in.")
    custom_loop.run_until_complete(quarter.logout())

# using logging instead of custom name is correct here.
custom_loop.run_until_complete(custom_loop.shutdown_asyncgens())
log.debug("Generators shutdown...")
asyncio.gather(*asyncio.Task.all_tasks()).cancel()
log.debug("All tasks canceled...")
custom_loop.stop()
log.debug("ASYNC loop halted. Killing log.")
# custom_loop.close()
logging.shutdown()

print("~~EOF~~")
raise SystemExit
