class AbstractWriter(object):

    # file reference

    def fileReference(self, path):
        raise NotImplementedError

    # language system

    def languageSystem(self, script, language):
        raise NotImplementedError

    # script

    def script(self, name):
        raise NotImplementedError

    # language

    def language(self, name, includeDefault=True):
        raise NotImplementedError

    # class definitiion

    def classDefinition(self, name, members):
        raise NotImplementedError

    # feature

    def newFeature(self, name):
        raise NotImplementedError

    # lookup

    def newLookup(self, name):
        raise NotImplementedError

    # lookup flag

    def lookupFlag(self, rightToLeft=False, ignoreBaseGlyphs=False, ignoreLigatures=False, ignoreMarks=False, markAttachmentType=None):
        raise NotImplementedError

    # feature reference

    def featureReference(self, name):
        raise NotImplementedError

    # lookup reference

    def lookupReference(self, name):
        raise NotImplementedError

    # GSUB

    def gsubSubtable(self, target, substitution, type, backtrack=[], lookahead=[]):
        """
        target is an ordered sequence of lists of glyph/class names
        substitution is an ordered sequence of lists of glyph/class names
        backtrack is an ordered sequence of lists of glyph/class names
        lookahead is an ordered sequence of lists of glyph/class names
        """
        raise NotImplementedError

    # GPOS

    def gposSubtable(self, target, positioning, backtrack=[], lookahead=[], type=None):
        raise NotImplementedError
