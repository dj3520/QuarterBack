import logging

log = logging.getLogger(__name__)

class command_matcher:
  def __init__(self):
    self.lookup = {}

  def reset(self):
    self.lookup = {}

  def add(self, match, to_return):
    if isinstance(match, list):
      for p in match:
        self.lookup[p] = to_return
        log.log(5, "Added "+str(p))
    else:
      self.lookup[match] = to_return
      log.log(5, "Added "+str(match))

  def match(self, match):
    log.debug("Try to match "+str(match))
    for k in self.lookup.keys():
      if match.startswith(k):
        return self.lookup[k]
    return None
