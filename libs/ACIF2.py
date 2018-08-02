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

<<<<<<< HEAD
  def get_list(self):
    return self.lookup.keys()

  def match(self, match, return_match=False):
=======
  def match(self, match):
>>>>>>> parent of 8266c11... match has optional return_math boolean
    log.debug("Try to match "+str(match))
    for k in self.lookup.keys():
      if match.startswith(k):
        return self.lookup[k]
    return None
