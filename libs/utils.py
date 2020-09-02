import discord
import re, math, collections

import logging

log = logging.getLogger(__name__)

def rreplace(s, old, new, occurrence):
  li = s.rsplit(old, occurrence)
  return new.join(li)

def starts_or_ends(text, test):
  return text.startswith(test) or text.endswith(test)

def caseless_remove(out, inp):
  if not out.lower() in inp.lower(): return inp
  if out.lower() in inp: return inp.replace(out.lower(), "")
  if out.capitalize() in inp: return inp.replace(out.capitalize(), "")
  if out in inp: return inp.replace(out, "")
  if out.upper() in inp: return inp.replace(out.upper(), "")

def remove_activation_text(message, sendback=False, convert=True):
  # Don't use clean_content. Harder to remove mentions
  out = message.content
  thisIsADM = is_pm(message.channel)

  # Grab bot user/member
  if thisIsADM:
    my_member = message.channel.me
  else:
    my_member = message.guild.me

  first_mention_of_me = True

  mentions = {}

  # Convert mentions to names
  for m in message.mentions:
    if m == my_member and first_mention_of_me:
      # m.mention text is not correct, no !
      out = out.replace("<@!" + str(m.id) + ">", '', 1)
      first_mention_of_me = False
    if thisIsADM:
      if convert: out = out.replace(m.mention, m.name)
    else:
      if convert: out = out.replace(m.mention, m.display_name)
      if not "members" in mentions.keys():
        mentions["members"] = []
      mentions["members"].append(m)
  for r in message.role_mentions:
    if convert: out = out.replace(r.mention, r.name)
    if not "roles" in mentions.keys():
      mentions["roles"] = []
    mentions["roles"].append(r)
  for c in message.channel_mentions:
    if convert: out = out.replace(c.mention, c.name)
    if not "channels" in mentions.keys():
      mentions["channels"] = []
    mentions["channels"].append(c)

  log.log(5, str(thisIsADM)+" and "+str(first_mention_of_me))
  # Match ONLY one, and if we haven't taken out a mention of ourself yet (we only want to remove one trigger)
  if first_mention_of_me and not thisIsADM:
    out = re.sub("(^"+my_member.name+"|\\b"+my_member.name+"$)", "", out, flags=re.IGNORECASE)

  if convert: out = out.replace("  ", " ")
  if not sendback: return out.strip()
  return [out.strip(), mentions]

def is_pm(place):
  return isinstance(place, discord.DMChannel)

def get_all_text_chans(every_chan):
  output = []
  for c in every_chan:
    if isinstance(c, discord.TextChannel): output.append(c)
  return output

def gonnacallyou(author):
  if isinstance(author, discord.Member):
    return author.display_name
  else:
    return author.name

def better_str(inthing):
  out = ''
  if isinstance(inthing, list) or isinstance(inthing, collections.abc.KeysView) or isinstance(inthing, collections.abc.ValuesView):
    for g in inthing:
      out+=str(g)+", "
  elif isinstance(inthing, float):
    out = "{:,.2f}".format(inthing)
    if len(out) < 1: return out
    while (out[-1] == "0" and "." in out):
      out=out[0:-1]
      if len(out) < 1: break
      if out[-1] == ".": return out[0:-1]
    return out
  elif isinstance(inthing, int): out = "{:,}".format(inthing)
  elif isinstance(inthing, type(None)): out = "~None~"
  else:
    out = str(inthing)
  return out

def bytesize(bytes):
  sizes = ["bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
  csel = 0
  obytes = bytes
  while obytes > 1280:
    obytes = math.floor(obytes / 1024)
    csel+=1
  if csel > len(sizes): return "[Overflow: Huge]"
  return str(obytes)+" "+sizes[csel]

def check_twitch_ignore(tid):
  # wizebot, nightbot, streamelements, moobot, cy_net (cyanide)
  bl = ["52268235", "19264788", "100135110", "1564983", "134826476"]
  return tid in bl
