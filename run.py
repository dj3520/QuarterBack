import time
starttime = time.time()

import discord
# from discord import opus

import asyncio, sys, math, datetime, unidecode
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

log.setLevel(5)

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
    await asyncio.sleep(0)
    if user.id == m.id: return m

async def get_guild_by_id(gid):
  out = []
  for g in quarter.guilds:
    await asyncio.sleep(0)
    if str(g.id) == str(gid): return g

async def send2owner(this):
  appinf = await quarter.application_info()
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
  await send2owner("I do not have `Add Reactions` permission in `"+message.guild.name+"/"+message.channel.name+"`")

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
  await send2owner("I do not have `"+want_perm+"` permission in `"+where.guild.name+"/"+where.name+"`")

async def write_message(where, content, tts=False):
  isEmbed = isinstance(content, discord.embeds.Embed)

  if isinstance(where, list):
    out = {}
    for i in where:
      await asyncio.sleep(0)
      out[i] = await write_message(i, content, tts=tts)
    return out

  if where == None:
    log.warning("Tried to send a message without a destination!")
    return

  if not isEmbed:
    if content == None: return False

    if len(content) > 2000:
      await write_message(where, "My reply was too long. (More than 2000 characters)")

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
    sent = await where.send(None, embed=content)
    return sent
  except discord.Forbidden:
    want_perm = "Embed Links"
    await failed_message(where, want_perm)
    return None

async def shutdown(dclient, message, match):
  await write_message(message.channel, "Goodbye.")
  await dclient.logout()

async def lvl_football(dclient, message, match):
  cleaned = message.clean_content.lower()
  log.debug(cleaned)
  cleaned = cleaned.replace("@quarterback "+match+" ", "")
  lvl = cleaned.split(" ")[0]
  log.debug(lvl)
  try: lvl = int(lvl)
  except: lvl = None
  football = settings.readSavedVar("football", default={})
  saved = 0
  if "football_kicks" in football.keys():
    saved = football["football_kicks"]
  if lvl == None:
    await write_message(message.channel, "Saved FootBall level is {}".format(saved))
    return
  football["football_kicks"] = lvl
  settings.setSavedVar("football", football)
  await write_message(message.channel, "Saved FootBall level is now {}".format(lvl))

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

    global ready_time
    ready_time = time.time()
    startedtime = math.trunc((ready_time - starttime) * 100) / 100
    logging.info("Started in "+str(startedtime)+" seconds.")
    logging.info(40*"=")

  async def on_member_leave(self, member):
    users = settings.readSavedVar("users", default={})
    if not str(member.id) in users.keys(): return
    if not users[str(member.id)] == False: return

    log.info("Football left stadium.")

    football = settings.readSavedVar("football", default={})

    # Save roles
    rl = []

    for m in member.roles:
      if m.is_default(): continue
      rl.append(str(m.id))

    football['football_roles'] = rl

    # Kick detection via audit log (find kicks for this user in the last 5 seconds)
    # Kick detection via audit log (find kicks for this user in the last 10 seconds)

    kick = False

    compare = datetime.datetime.utcnow() + datetime.timedelta(seconds=10)
    alog = await member.server.audit_logs(before=compare)
    log.debug("{} Audit log entries in last 10 seconds.".format(len(alog)))
    for e in alog:
      if e.action == discord.AuditLogAction.kick or e.action == discord.AuditLogAction.ban:
        if target.id == member.id:
          kick = True
          break

    log.info("Kick detection reads {}".format(kick))

    # Increase counter on kick
    if kick:
      if "football_kicks" in football.keys():
        football["football_kicks"] += 1

    # Save
    settings.setSavedVar("football", football)

  async def on_member_join(self, member):

    users = settings.readSavedVar("users", default={})

    if "discord.gg/" in member.name:
      await member.kick(reason="Username includes discord invite link.")
      users[str(member.id)] = "[Automatic] Username included discord invite link."
      settings.setSavedVar("users", users)
      await do_warn(member, "Automatically kicked due to discord invite link in username. Please remove any automated welcome messages.")
      return

    log.info("{} joined the {} server".format(member.id, member.guild.name))
    ret = None
    if str(member.id) in users.keys(): ret = users[str(member.id)]
    if "{} in {}".format(member.id, member.guild.id) in users.keys(): ret = users["{} in {}".format(member.id, member.guild.id)]
    if ret == None: return
    log.log(5, "Found an entry for this user: {}".format(ret))
    if ret == False:
      await charlotte(member)
      return
    await do_warn(member, ret)
    delta = datetime.datetime.utcnow() - member.created_at
    delta = delta.total_seconds()
    log.debug("Account age in seconds: {}".format(delta))
    if delta < 2678400: await do_warn(member, "Account is less than 31 days old.")

  async def on_guild_join(self, guild):
    log.info(guild.name+" joined!")
    await send2owner(guild.name+" joined!")

  async def on_member_update(self, old, new):
    if old.bot: return

    users = settings.readSavedVar("users", default={})
    if str(new.id) in users.keys():
      if users[str(new.id)].startswith("NAME_LOCK"):
        nick = users[str(new.id)].replace("NAME_LOCK ", "")
        if new.nick == old.nick: return
        if not new.nick == nick:
          try: await new.edit(nick=nick, reason="Name lock enabled for this user.")
          except: pass

  async def on_message(self, message):
    appinf = await quarter.application_info()
    owner = message.author.id == appinf.owner.id and (self.user in message.mentions or utils.is_pm(message.channel))
    requested = message.content.startswith("qb ")

    # Ignore own messages
    if message.author == self.user: return

    # Ignore bots
    if message.author.bot: return

    if isinstance(message.content.lower(), str):
      check1 = ACIF2.command_matcher()
      check1.add("sweetiestarr", "Unwritten rule was broken.")
      #11. Absolutely no Uganda Knuckles talk.
      check1.add(["ebola", "da wey", "uganda", "ugandan knuckles", "da wei", "de wei", "de way"], "Possible Rule 11.")
      # 9. No talk of religion
      # nothing yet
      # 8. No talk of politics.
      check1.add(["bipartisan", "caucus", "filibuster", "gerrymander", "politics", "republican", "democrat"], "Possible Rule 8.")

      do = check1.match(message.content.lower())
      if isinstance(do, str):
        message_link = "https://discordapp.com/channels/{}/{}/{}".format(message.guild.id, message.channel.id, message.id)
        await do_warn(message.author, "{}\nChannel: <#{}>\n{}".format(do, message.channel.id, message_link))
      elif not do == None:
        await do(self, message, match)

    users = settings.readSavedVar("users", default={})
    if str(message.author.id) in users.keys():
      if users[str(message.author.id)] == "HECK":

        # _should_ convert most accent marks
        conv = message.content.lower()
        conv = conv.replace(":regional_indicator_", "")
        # Need to take off the other colon too
        conv = conv.replace(":", "")

        for i in range(0, 3):
          conv = conv.replace("heck"[i]*2, "heck"[i])

        conv2 = unidecode.unidecode(conv)

        # Feel free to append
        heck_check = ["heck", "ʞɔǝɥ", "ʰᵉᶜᵏ", "h3ck", "həck"]

        has_heck = False
        for i in heck_check:
          if i.lower() in conv or i.lower() in conv2:
            has_heck = True
            break

        if has_heck:
          try:
            await message.add_reaction(chr(127469))
            await message.add_reaction(chr(127466))
            await message.add_reaction(chr(127464))
            await message.add_reaction(chr(127472))
          except:
            pass

    # Ignore normal messages
    if not owner and not requested: return

    # Ignore DMs from non-owner
    if utils.is_pm(message.channel) and not owner: return

    check = ACIF2.command_matcher()
    if owner:
      cleaned = utils.remove_activation_text(message, sendback=True)
      mentions = cleaned[1]
      cleaned = cleaned[0]
      check.add("sudo reboot", shutdown)
    elif requested:
      cleaned = message.content.replace("qb ", "")
      check.add("ping", "Pong!")
      if message.author.guild_permissions.manage_roles:
        check.add("dump roles", dump_roles)
      if message.author.guild_permissions.kick_members:
        check.add("add", add_warn)
        check.add("set", set_warn)
        check.add("scan", rescan)
        check.add("lvl football", lvl_football)

    check.add(["list commands", "help"], utils.better_str(check.get_list()))

    do, match = check.match(cleaned.lower(), return_match=True)
    if isinstance(do, str):
      await write_message(message.channel, do)
    elif not do == None:
      await do(self, message, match)

## === ~~~ -- Commands -- ~~~ === ##

async def charlotte(charl):
  football = settings.readSavedVar("football", default={})
  try:
    if "football_roles" in football.keys():
      tack_on = []
      for i in football["football_roles"]:
        for r in charl.guild.roles:
          if i == str(r.id): tack_on.append(r)
      await charl.edit(reason="Welcome back football!", roles=tack_on)
    if "football_kicks" in football.keys():
      await charl.edit(reason="Welcome back football!", nick="FootBall Lvl "+str(football["football_kicks"]))
  except Exception as e:
    log.warning("Something went wrong! What gives?")
    log.exception(e)

async def rescan(dclient, message, match):
  if utils.is_pm(message.channel):
    await write_message(message.channel, "This is a private message. Do the command in a server.")
    return

  users = settings.readSavedVar("users", default={})
  compiled = ""
  for m in message.guild.members:
    ret = None
    if str(m.id) in users.keys(): ret = users[str(m.id)]
    if "{} in {}".format(m.id, message.guild.id) in users.keys(): ret = users["{} in {}".format(m.id, message.guild.id)]
    if ret == None: continue
    if ret == False: ret = "Is a football."
    compiled = "{}{} - {}\n".format(compiled, m.mention, ret)
  if compiled == "":
    await write_message(message.channel, "No users found with warnings in this server. :thumbsup:")
    return
  await write_message(message.channel, compiled)

async def do_warn(member, reason):
  guild = member.guild
  channel = await get_guild_setting(guild.id, "warn-channel")
  msg = member.mention+" - "+reason
  if channel == None:
    await write_message(guild.owner, "Warning channel isn't configured.\n"+msg)
    return
  channel = guild.get_channel(channel)
  if channel == None:
    await write_message(guild.owner, "Warning channel wasn't found.\n"+msg)
    return
  await write_message(channel, msg)

async def add_warn(dclient, message, match):
  guild = message.guild
  channel = await get_guild_setting(guild.id, "warn-channel")
  if channel == None:
    await write_message(message.channel, "Warning channel isn't configured.")
  else:
    channel = guild.get_channel(channel)
    if channel == None:
      await write_message(message.channel, "Warning channel wasn't found.\n"+msg)

  cleaned = message.clean_content
  cleaned = cleaned.replace("qb add ", "")
  uid = cleaned.split(" ")[0]
  cleaned = cleaned.replace(uid, "")
  cleaned = cleaned.strip()

  clear = cleaned == "clear"
  users = settings.readSavedVar("users", default={})

  if cleaned.startswith("NAME_LOCK"):
    if len(cleaned.replace("NAME_LOCK ", "")) > 33:
      await write_message(message.channel, ":x: Locked name is above 32 characters.")
      return

  if clear:
    log.info("Clearing warn: {} Old reason: {}".format(uid, users[uid]))
    del users[uid]
    await write_message(message.channel, ":ok_hand:")
  else:
    log.info("New warn: {} Reason: {}".format(uid, cleaned))
    users[uid] = cleaned
    await write_message(message.channel, ":thumbsup:")
  settings.setSavedVar("users", users)

async def set_warn(dclient, message, match):
  guild = message.guild
  channel = message.channel_mentions
  if len(channel) > 1:
    await write_message(message.channel, "More than one channel supplied. This is not supported.")
    return

  channel = channel[0]

  await set_guild_setting(guild.id, "warn-channel", int(channel.id))
  await write_message(channel, ":thumbsup:")

async def dump_roles(dclient, message, match):
  if utils.is_pm(message.channel):
    await write_message(message.channel, "This is a private message. Do the command in a server.")
    return
  await write_message(message.channel, "```"+utils.better_str([str(r.id)+" - "+r.name for r in message.guild.role_hierarchy]).replace(", ", "\n")+"```")


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
