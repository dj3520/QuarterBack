import logging, json, os, copy

log = logging.getLogger(__name__)

class SaveSys:
  def __init__(self, file, ds = False):
    self.settingsFile = file
    self.settingsDic = {}
    self.disksaver = ds
    if os.path.isfile(self.settingsFile):
      with open(self.settingsFile, encoding="utf8") as f:
        self.settingsDic = json.load(f)

  # These allow using this lib in WITH statements
  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    del self

  def readSavedVar(self, var, default=None):
    log.log(4, "["+self.settingsFile+"] Reading value: "+var)

    if var in self.settingsDic:
      return self.settingsDic[var]
    return default

  def setSavedVar(self, var, val):

    if self.disksaver:
      if var in self.settingsDic.keys():
        if self.settingsDic[var] == val:
          log.log(4, "[{}] Not updating '{}' because it's the same as before.".format(self.settingsFile, var))
          return

    # Change in memory, then dump memory
    log.log(5, "[{}] Saving value to vars: {} = {}".format(self.settingsFile, var, val))
    if isinstance(val, dict): self.settingsDic[var] = copy.deepcopy(val)
    elif isinstance(val, list): self.settingsDic[var] = val.copy()
    else: self.settingsDic[var] = val

    self.saveToDisk()

  def delSavedVar(self, var):
    if not var in self.settingsDic.keys(): return False

    # Change in memory, then dump memory
    log.log(5, "["+self.settingsFile+"] Deleting value: "+var)
    del self.settingsDic[var]

    self.saveToDisk()

  def saveToDisk(self):
    log.log(4, "["+self.settingsFile+"] Saving this amount of vars to disk: "+str(len(self.settingsDic)))
    if len(self.settingsDic) == 0:
      if os.path.isfile(self.settingsFile):
        log.debug("["+self.settingsFile+"] Save file will not contain any information, so deleting it.")
        try: os.remove(self.settingsFile)
        except:
          log.critical("Failed to delete "+self.settingsFile)
          log.exception(e)
    else:
      moment = self.settingsFile+".tmp"
      try:
        with open(moment, "w", encoding="utf8") as f:
          json.dump(self.settingsDic, f, sort_keys=True, indent=2)
      except Exception as e:
        if os.path.isfile(moment):
          os.remove(moment)
        log.critical("Failed to save "+self.settingsFile)
        log.exception(e)
        return
      if os.path.isfile(self.settingsFile): os.remove(self.settingsFile)
      os.rename(moment, self.settingsFile)
    return
