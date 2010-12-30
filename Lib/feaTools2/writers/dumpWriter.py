class DumpWriter(object):

    def __init__(self):
        self._content = []
        self._inScript = False
        self._inLanguage = False
        self._indent = 0

    def dump(self):
        text = self._dump()
        return "\n".join(text)

    def _dump(self):
        text = []
        for item in self._content:
            if isinstance(item, self.__class__):
                text += item._dump()
            else:
                text.append(item)
        return text

    def _getIndentCount(self):
        return self._inScript + self._inLanguage + self._indent

    def _addLine(self, text):
        indent = "    " * self._getIndentCount()
        text = indent + text
        text = text.rstrip()
        self._content.append(text)

    def _flattenList(self, items):
        result = []
        for item in items:
            if isinstance(item, basestring):
                pass
            else:
                item = "[%s]" % self._flattenList(item)
            result.append(item)
        return " ".join(result)

    # file reference

    def fileReference(self, path):
        # this shouldn't happen in the objects
        raise NotImplementedError

    # language system

    def languageSystem(self, script, language):
        self._addLine("LanguageSystem: %s %s" % (script, language))

    # script

    def script(self, name):
        self._inScript = False
        self._inLanguage = False
        self._addLine("Script: %s" % name)
        self._inScript = True

    # language

    def language(self, name, includeDefault=True):
        self._inLanguage = False
        self._addLine("Language: %s" % name)
        self._inLanguage = True
        self._addLine("Include Default: %s" % includeDefault)

    # class definitiion

    def classDefinition(self, name, members):
        self._addLine("Class: %s: [%s]" % (name, " ".join(members)))

    # feature

    def newFeature(self, name):
        self._addLine("Feature: %s" % name)
        # make the new writer
        writer = self.__class__()
        writer._indent = self._getIndentCount() + 1
        self._content.append(writer)
        return writer

    # lookup

    def newLookup(self, name):
        self._addLine("Lookup: %s" % name)
        # make the new writer
        writer = self.__class__()
        writer._indent = self._getIndentCount() + 1
        self._content.append(writer)
        return writer

    # lookup flag

    def lookupFlag(self, rightToLeft=False, ignoreBaseGlyphs=False, ignoreLigatures=False, ignoreMarks=False, markAttachmentType=None):
        self._addLine("LookupFlag:")
        self._indent += 1
        text = [
            "rightToLeft: %s" % rightToLeft,
            "ignoreBaseGlyphs: %s" % ignoreBaseGlyphs,
            "ignoreLigatures: %s" % ignoreLigatures,
            "ignoreMarks: %s" % ignoreMarks,
            "markAttachmentType: %s" % markAttachmentType
        ]
        for line in text:
            self._addLine(line)
        self._indent -= 1

    # feature reference

    def featureReference(self, name):
        self._addLine("Feature Reference: %s" % name)

    # lookup reference

    def lookupReference(self, name):
        self._addLine("Lookup Reference: %s" % name)

    # GSUB

    def gsubSubtable(self, target, substitution, type, backtrack=[], lookahead=[]):
        self._addLine("GSUBSubtable Type %d:" % type)
        self._indent += 1
        text = [
            "backtrack: [%s]" % self._flattenList(backtrack),
            "lookahead: [%s]" % self._flattenList(lookahead),
            "target: [%s]" % self._flattenList(target),
            "substitution: [%s]" % self._flattenList(substitution)
        ]
        for line in text:
            self._addLine(line)
        self._indent -= 1
        

    # GPOS

    def gposSubtable(self, target, positioning, backtrack=[], lookahead=[], type=None):
        pass
