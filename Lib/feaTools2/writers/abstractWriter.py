class AbstractWriter(object):

    # file reference

    def addFileReference(self, path):
        raise NotImplementedError

    # language system

    def addLanguageSystem(self, script, language):
        raise NotImplementedError

    # script

    def addScript(self, name):
        raise NotImplementedError

    # language

    def addLanguage(self, name, includeDefault=True):
        raise NotImplementedError

    # class definitiion

    def addClassDefinition(self, name, members):
        raise NotImplementedError

    # feature

    def addFeature(self, name):
        raise NotImplementedError

    # lookup

    def addLookup(self, name):
        raise NotImplementedError

    # lookup flag

    def addLookupFlag(self, rightToLeft=False, ignoreBaseGlyphs=False, ignoreLigatures=False, ignoreMarks=False, markAttachmentType=None):
        raise NotImplementedError

    # feature reference

    def addFeatureReference(self, name):
        raise NotImplementedError

    # lookup reference

    def addLookupReference(self, name):
        raise NotImplementedError

    # GSUB

    def addGSUBSubtable(self, target, substitution, type, backtrack=[], lookahead=[]):
        raise NotImplementedError

    # GPOS

    def addGPOSSubtable(self, target, positioning, backtrack=[], lookahead=[], type=None):
        raise NotImplementedError
