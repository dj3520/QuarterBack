import asyncio
import logging

log = logging.getLogger(__name__)

class role_giver:

  def __init__(self, config, cat, **kwargs):
    self.config = config
    self.cat = cat

  async def role_give(self, message, args):
    await message.delete()
    chooser = self.cat.command_matcher()
    for k, v in self.config['sar-ids'].items():
      for r in message.guild.roles:
        if r.id == v:
          chooser.add(k, r)
          break

    do = chooser.match(args[1])
    if do == None: return "Can't find that role. Options are {}".format(set(self.config['sar-ids'].keys()))

    log.debug("Attempting to give role {} to member {}".format(r.name, message.author.name))
    try:
      await message.author.add_roles(do)
      return ":thumbsup:"
    except:
      return "Was a problem with that. Make sure bot's priviliges include role giving."


  async def add_role(self, message, args):

    if 'sar-ids' in self.config.keys():
      for k, v in self.config['sar-ids'].items():
        if k == args[1]: return "Already have a SAR with name {}".format(k)
        if v == args[2]: return "Already have a SAR with ID {} ({})".format(v, k)
    else:
      self.config['sar-ids'] = {}
    try:
      self.config['sar-ids'][args[1]] = int(args[2])
    except:
      return "Was a problem with that. Make sure second argument is number."
    return self.config

  async def on_message(self, message, owner, text):
    chooser = self.cat.command_matcher()

    right_channel = 'role-choose-channel' in self.config.keys()
    if right_channel: right_channel = message.channel.id == self.config['role-choose-channel']

    if right_channel or owner:
      chooser.add("join ", self.role_give)
    if owner:
      chooser.add("include-sar ", self.add_role)

    do, match = chooser.match(text, return_match=True)

    cleaned = text
    cleaned = cleaned.replace("{} ".format(match), "")
    uid = cleaned.split(" ")

    if do == None: return
    sb = await do(message, uid)
    return sb
