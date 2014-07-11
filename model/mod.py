from itertools import chain, imap
import os
from tempfile import mkdtemp
from zipfile import ZipFile

from parsers.files import parse_file
from tools.paths import get_path_components, get_unix_path

import settings


class InvalidMod(Exception):
    pass


def get_default_mods_directory():
    # assume windows and fairies and pixie dust for now
    # in particular, this will fail for:
    #  (1) old OSs (which use 'My Documents')
    #  (2) anyone who moved the documents folder
    #  (3) good operating systems :)
    return os.path.join(os.path.expanduser('~'), 'Documents',
            'Paradox Interactive', 'Europa Universalis IV', 'mod')


class Mod(object):
    def __init__(self, mod, modDir=''):
        if mod:
            if not modDir:
                modDir = get_default_mods_directory()

            if not mod.endswith('.mod'):
                mod += '.mod'

            modFile = os.path.join(modDir, mod)

            if not os.path.isfile(modFile):
                raise InvalidMod('Could not find mod file at %s'%modFile)

            with open(modFile, 'rU') as f:
                self.modData = parse_file(f)

            self.modDir = modDir
        else:
            self.modData = None

    @staticmethod
    def getRelativeModPath(s):
        modPath = get_path_components(s)
        
        assert modPath[0] == 'mod'
        modPath = modPath[1:]

        return os.path.join(*modPath)

    @property
    def _modPath(self):
        modPath = self.getRelativeModPath(self.modData['path'])
        return os.path.join(self.modDir, modPath)

    @property
    def _archivePath(self):
        modPath = self.getRelativeModPath(self.modData['archive'])
        return os.path.join(self.modDir, modPath)

    def _open(self, filePath, mode='rU'):
        # first, try to load the file from the mod
        if self.modData is not None:
            if 'archive' in self.modData:
                with ZipFile(self._archivePath, 'r') as zf:
                    # zipfile requires Unix paths ><
                    uFilePath = get_unix_path(filePath)

                    try:
                        try:
                            return zf.open(uFilePath, mode)
                        except RuntimeError:
                            # NB: should delete this, but don't atm
                            tmpDirPath = mkdtemp()
                            mapPath = zf.extract(uFilePath, tmpDirPath)
                            return open(mapPath, mode)
                    except KeyError: # no such file in mod
                        pass
            elif 'path' in self.modData:
                modFilePath = os.path.join(self._modPath, filePath)
                
                # try to open the file at the mod path
                try:
                    return open(modFilePath, mode)
                except IOError:
                    pass # no such file in mod

                # fall through to getting the file from the eu4 directory

        defaultFilePath = os.path.join(settings.eu4_directory, filePath)

        return open(defaultFilePath, mode)

    def open(self, *path, **kwargs):
        return self._open(os.path.join(*path), **kwargs)
    
    @property
    def mapImageFile(self):
        return self.open('map', 'provinces.bmp', mode='rb')

    @property
    def mapSettingsFile(self):
        return self.open('map', 'default.map')

    @property
    def provinceDefinitionFile(self):
        return self.open('map', 'definition.csv')

    def iterdir(self, *path):
        it = self._iterdir(*path)

        while 1:
            with it.next() as f:
                yield f

    def _iterdir(self, *path):
        # there are two key rules:
        #  (1) if a file appears in the mod, it takes priority
        #  (2) if a directory is marked with replace_path, no files from the
        #      eu4 version of that directory should be used
        eu4Path = os.path.join(settings.eu4_directory, *path)
        eu4Filenames = os.listdir(eu4Path)

        fAppendPath = lambda start: lambda p: os.path.join(start, p)
        eu4Files = map(fAppendPath(eu4Path), eu4Filenames)

        # we need to remove any subfolders (assumption is that this is a non
        # recursive iteration)
        eu4Files = filter(os.path.isfile,  eu4Files)
        eu4Filenames = map(os.path.basename, eu4Files)

        if self.modData is None:
            return imap(open, eu4Files)

        # normalise in case one thing uses backslashes and the other forward
        fNormalisePath = lambda p: os.path.join(*get_path_components(p))
        fNotIn = lambda seq: lambda v: v not in seq

        eu4Files = map(fNormalisePath, eu4Files)

        # now handle replace_path
        if 'replace_path' in self.modData:
            rp = self.modData['replace_path']
            replacePaths = rp if isinstance(rp, list) else [rp]
            excludedPaths = map(fNormalisePath, replacePaths)

            # NB: assuming path fragments can't repeat
            # eg, would fail on /ok/path/uhoh/excluded/path/but/at/end
            fValidPath = lambda p: not any(ep in p for ep in excludedPaths)

            eu4Files = filter(fValidPath, eu4Files)

        if 'archive' in self.modData:
            with ZipFile(self._archivePath, 'r') as zf:
                allPaths = map(fNormalisePath, zf.namelist())

                relPath = os.path.join(*path)
                validPaths = filter(lambda p: p.startswith(relPath), allPaths)

                archiveFilenames = map(os.path.basename, validPaths) 
                filenames = set(archiveFilenames).union(eu4Filenames)
        elif 'path' in self.modData:
            modPath = os.path.join(self._modPath, *path)

            if not os.path.exists(modPath):
                return eu4Files

            modFilenames = os.listdir(modPath)
            filenames = set(modFilenames).union(eu4Filenames)

        paths = map(lambda fn: os.path.join(*(path + (fn,))), filenames)

        return imap(self.open, paths)
