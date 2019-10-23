import logging, json, os, copy

log = logging.getLogger(__name__)

class SaveSys:
  def __init__(self, ifile, ds = True):
    self.settingsFile = ifile
    self.settingsDic = {}
    self.disksaver = ds
    if os.path.isfile(self.settingsFile):
      with open(self.settingsFile, encoding="utf8") as f:
        self.istr = f.read()

      self.settingsDic = json.loads(self.istr)

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
    self.settingsDic[var] = val
    self.saveToDisk()

  def delSavedVar(self, var):
    if not var in self.settingsDic.keys(): return False

    self.saveToDisk()
    return True

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
      ostr = json.dumps(self.settingsDic, sort_keys=True, indent=2)
      if ostr == self.istr: return

      moment = self.settingsFile
      if not self.disksaver:
        moment = moment+".tmp"
      try:
        with open(moment, "w", encoding="utf8") as f:
          f.write(ostr)
      except Exception as e:
        if not disksaver and os.path.isfile(moment):
          os.remove(moment)
        log.critical("Failed to save "+self.settingsFile)
        log.exception(e)
        return
      if not self.disksaver:
        if os.path.isfile(self.settingsFile): os.remove(self.settingsFile)
        os.rename(moment, self.settingsFile)

