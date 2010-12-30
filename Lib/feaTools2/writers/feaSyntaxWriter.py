from abstractWriter import AbstractWriter


defaultLookupFlag = dict(
    rightToLeft=False,
    ignoreBaseGlyphs=False,
    ignoreLigatures=False,
    ignoreMarks=False,
    markAttachmentType=False
)


needSpaceBefore = "feature lookup script language lookupReference".split(" ")
needSpaceAfter = "feature lookup script language lookupReference".split(" ")


class FeaSyntaxWriter(AbstractWriter):

    def __init__(self, whitespace="\t", filterRedundancies=False):
        self._whitespace = whitespace
        self._indent = 0
        self._filter = filterRedundancies
        self._content = []
        self._text = []
        self._identifierStack = []
        self._initialLookupFlag = defaultLookupFlag
        self._inScript = False
        self._inLanguage = False

    # ------
    # Output
    # ------

    def write(self):
        if self._filter:
            self._preWrite()
        text = self._basicWrite()
        return "\n".join(text)

    def _basicWrite(self):
        text = []
        for item in self._text:
            if isinstance(item, self.__class__):
                text += item._basicWrite()
            else:
                text.append(item)
        text += self._handleFinalBreak()
        return text

    def _preWrite(self):
        # filter
        self._filterContent()
        # reset he indents
        self._inScript = False
        self._inLanguage = False
        # write
        for item in self._content:
            kwargs = dict(item)
            identifier = kwargs.pop("identifier")
            if identifier in ("newFeature", "newLookup"):
                writer = kwargs["writer"]
                writer._indent = self._indentLevel() + 1
                writer._preWrite()
            methodName = "_" + identifier
            method = getattr(self, methodName)
            method(**kwargs)

    # white space

    def _handleBreakBefore(self, identifier):
        # always need break
        if identifier in needSpaceBefore:
            self._text.append("")
        # sequence break
        elif self._identifierStack and identifier != self._identifierStack[-1]:
            self._text.append("")

    def _handleFinalBreak(self):
        text = []
        if not self._identifierStack:
            pass
        elif self._identifierStack[-1] in needSpaceAfter:
            text = [""]
        return text

    def _indentLevel(self):
        return self._inScript + self._inLanguage + self._indent

    def _indentText(self, text):
        indentLevel = self._indentLevel()
        indent = self._whitespace * indentLevel
        new = []
        for i in text:
            new.append(indent + i)
        return new

    # flattening

    def _flattenItem(self, item):
        if isinstance(item, basestring):
            return item
        final = []
        for i in item:
            if not isinstance(i, basestring):
                i = "[%s]" % self._flattenItem(i)
            final.append(i)
        return " ".join(final)

    # ---------
    # Filtering
    # ---------

    def _filterContent(self):
        self._newContent = []
        while self._content:
            item = self._content.pop(0)
            identifier = item["identifier"]
            # script
            if identifier == "script":
                item = self._filterScript(item)
            # language
            elif identifier == "language":
                item = self._filterLanguage(item)
            # lookup flag
            elif identifier == "lookupFlag":
                item = self._filterLookupFlag(item)
            # store
            if item is not None:
                self._newContent.append(item)
        self._content = self._newContent
        del self._newContent

    def _filterScript(self, item):
        needScript = False
        while not needScript:
            # write DFLT only if the script is being
            # declared after a lookup or subtable
            if item["name"] == "DFLT":
                needScript = False
                for otherItem in self._newContent:
                    identifier = otherItem["identifier"]
                    # lookup
                    if identifier.startswith("lookup"):
                        needScript = True
                    # subtable
                    elif identifier == "gsubSubtable":
                        needScript = True
                    elif identifier == "gposSubtable":
                        needScript = True
                break
            # don't write the script if no lookups or subtables are
            # between this script and the end of the scope
            # or another script declaration.
            else:
                for otherItem in self._content:
                    identifier = otherItem["identifier"]
                    # lookup or lookup reference
                    if identifier.startswith("lookup"):
                        needScript = True
                    # subtable
                    elif identifier == "gsubSubtable":
                        needScript = True
                    elif identifier == "gposSubtable":
                        needScript = True
                    # script
                    elif identifier == "script":
                        needScript = False
                        break
                break
        if needScript:
            return item

    def _filterLanguage(self, item):
        needLanguage = False
        while not needLanguage:
            # write dflt only if the language is being
            # declared after a lookup or subtable
            if item["name"] is None:
                needScript = False
                for otherItem in self._newContent:
                    identifier = otherItem["identifier"]
                    # script
                    # if a script occurs before any of the above,
                    # the language is not needed
                    if identifier == "script":
                        needLanguage = False
                        break
                break
            # don't write the language if no lookups or subtables are
            # between this script and the end of the scope
            # or another language declaration.
            else:
                for otherItem in self._content:
                    identifier = otherItem["identifier"]
                    # lookup or lookup reference
                    if identifier.startswith("lookup"):
                        needLanguage = True
                    # subtable
                    elif identifier == "gsubSubtable":
                        needLanguage = True
                    elif identifier == "gposSubtable":
                        needLanguage = True
                    # script
                    elif identifier == "script":
                        needLanguage = True
                break
        if needLanguage:
            return item

    def _filterLookupFlag(self, item):
        currentFlag = self._findCurrentLookupFlag(self._newContent)
        newFlag = dict(item)
        del newFlag["identifier"]
        if newFlag == currentFlag:
            return None
        return item

    # ---------
    # Appending
    # ---------

    # file reference

    def fileReference(self, path):
        # don't filter
        if not self._filter:
            self._fileReference(path)
            return
        # filter
        d = dict(
            identifier="fileReference",
            path=path
        )
        self._content.append(d)

    def _fileReference(self, path):
        self._handleBreakBefore("fileReference")
        text = [
            "include(%s);" % path
        ]
        self._text += self._indentText(text)
        self._identifierStack.append("fileReference")

    # language system

    def languageSystem(self, script, language):
        # don't filter
        if not self._filter:
            self._languageSystem(script, language)
            return
        # filter
        d = dict(
            identifier="languageSystem",
            script=script,
            language=language
        )
        self._content.append(d)

    def _languageSystem(self, script, language):
        if language is None:
            language = "dflt"
        language = language.strip()
        self._handleBreakBefore("languageSystem")
        text = [
            "languagesystem %s %s;" % (script, language)
        ]
        self._text += self._indentText(text)
        self._identifierStack.append("languageSystem")

    # script

    def script(self, name):
        # don't filter
        if not self._filter:
            self._script(name)
            return
        # filter
        d = dict(
            identifier="script",
            name=name
        )
        self._content.append(d)
        # shift the indents
        self._inScript = True
        self._inLanguage = False

    def _script(self, name):
        # shift the indents back
        self._inScript = False
        self._inLanguage = False
        # write
        self._handleBreakBefore("script")
        text = [
            "script %s;" % name
        ]
        self._text += self._indentText(text)
        # shift the following lines
        self._inScript = True
        # done
        self._identifierStack.append("script")

    # language

    def language(self, name, includeDefault=True):
        # don't filter
        if not self._filter:
            self._language(name, includeDefault)
            return
        # filter
        d = dict(
            identifier="language",
            name=name,
            includeDefault=includeDefault
        )
        self._content.append(d)
        # shift the indents
        self._inLanguage = True

    def _language(self, name, includeDefault=True):
        # shift the indent back
        self._inLanguage = False
        # write
        if name is None:
            name = "dflt"
        name = name.strip()
        self._handleBreakBefore("language")
        text = [
            "language %s;" % name
        ]
        self._text += self._indentText(text)
        # shift the following lines
        self._inLanguage = True
        # done
        self._identifierStack.append("language")

    # class definitiion

    def classDefinition(self, name, members):
        # don't filter
        if not self._filter:
            self._classDefinition(name, members)
            return
        # filter
        d = dict(
            identifier="classDefinition",
            name=name,
            members=members
        )
        self._content.append(d)

    def _classDefinition(self, name, members):
        self._handleBreakBefore("classDefinition")
        text = [
            "%s = [%s];" % (name, self._flattenItem(members))
        ]
        self._text += self._indentText(text)
        self._identifierStack.append("classDefinition")

    # feature

    def newFeature(self, name):
        writer = self.__class__(whitespace=self._whitespace, filterRedundancies=self._filter)
        writer._indent = self._indent + 1
        # don't filter
        if not self._filter:
            self._newFeature(name, writer)
            return writer
        # filter
        d = dict(
            identifier="newFeature",
            name=name,
            writer=writer
        )
        self._content.append(d)
        return writer

    def _newFeature(self, name, writer):
        self._handleBreakBefore("feature")
        # start
        s = "feature %s {" % name
        self._text += self._indentText([s])
        # store the new writer
        self._text.append(writer)
        # close
        s = "} %s;" % name
        self._text += self._indentText([s])
        self._identifierStack.append("feature")

    # lookup

    def newLookup(self, name):
        writer = self.__class__(whitespace=self._whitespace, filterRedundancies=self._filter)
        writer._indent = self._indentLevel()
        # don't filter
        if not self._filter:
            self._newLookup(name, writer)
            return writer
        # filter
        writer._initialLookupFlag = self._findCurrentLookupFlag(self._content)
        d = dict(
            identifier="newLookup",
            name=name,
            writer=writer
        )
        self._content.append(d)
        return writer

    def _newLookup(self, name, writer):
        self._handleBreakBefore("lookup")
        # start
        s = "lookup %s {" % name
        self._text += self._indentText([s])
        # store the new writer
        self._text.append(writer)
        # close
        s = "} %s;" % name
        self._text += self._indentText([s])
        self._identifierStack.append("lookup")
        return writer

    # lookup flag

    def _findCurrentLookupFlag(self, content):
        for item in reversed(content):
            identifier = item["identifier"]
            if identifier == "lookupFlag":
                d = dict(item)
                del d["identifier"]
                return d
            elif identifier == "script":
                return defaultLookupFlag
        return self._initialLookupFlag

    def lookupFlag(self, rightToLeft=False, ignoreBaseGlyphs=False, ignoreLigatures=False, ignoreMarks=False, markAttachmentType=None):
        # don't filter
        if not self._filter:
            self._lookupFlag(rightToLeft, ignoreBaseGlyphs, ignoreLigatures, ignoreMarks, markAttachmentType)
            return
        # filter
        d = dict(
            identifier="lookupFlag",
            rightToLeft=rightToLeft,
            ignoreBaseGlyphs=ignoreBaseGlyphs,
            ignoreLigatures=ignoreLigatures,
            ignoreMarks=ignoreMarks,
            markAttachmentType=markAttachmentType
        )
        self._content.append(d)

    def _lookupFlag(self, rightToLeft=False, ignoreBaseGlyphs=False, ignoreLigatures=False, ignoreMarks=False, markAttachmentType=None):
        self._handleBreakBefore("lookupFlag")
        values = []
        if rightToLeft:
            values.append("RightToLeft")
        if ignoreBaseGlyphs:
            values.append("IgnoreBaseGlyphs")
        if ignoreLigatures:
            values.append("IgnoreLigatures")
        if ignoreMarks:
            values.append("IgnoreMarks")
        if not values:
            values.append("0")
        values = ", ".join(values)
        text = [
            "lookupflag %s;" % values
        ]
        self._text += self._indentText(text)
        self._identifierStack.append("lookupFlag")

    # feature reference

    def featureReference(self, name):
        # don't filter
        if not self._filter:
            self._featureReference(name)
            return
        # filter
        d = dict(
            identifier="featureReference",
            name=name
        )
        self._content.append(d)

    def _featureReference(self, name):
        raise NotImplementedError

    # lookup reference

    def lookupReference(self, name):
        # don't filter
        if not self._filter:
            self._lookupReference(name)
            return
        # filter
        d = dict(
            identifier="lookupReference",
            name=name
        )
        self._content.append(d)

    def _lookupReference(self, name):
        self._handleBreakBefore("lookupReference")
        text = [
            "lookup %s;" % name
        ]
        self._text += self._indentText(text)
        self._identifierStack.append("lookupReference")

    # GSUB

    def gsubSubtable(self, target, substitution, type, backtrack=[], lookahead=[]):
        assert isinstance(target, list)
        assert isinstance(substitution, list)
        assert isinstance(backtrack, list)
        assert isinstance(lookahead, list)
        # don't filter
        if not self._filter:
            self._gsubSubtable(target, substitution, type, backtrack, lookahead)
            return
        # filter
        d = dict(
            identifier="gsubSubtable",
            type=type,
            target=target,
            substitution=substitution,
            backtrack=backtrack,
            lookahead=lookahead
        )
        self._content.append(d)

    def _gsubSubtable(self, target, substitution, type, backtrack=[], lookahead=[]):
        self._handleBreakBefore("gsubSubtable")
        item = dict(
            target=target,
            substitution=substitution,
            type=type,
            backtrack=backtrack,
            lookahead=lookahead
        )
        method = getattr(self, "_writeGSUBSubtableType%d" % type)
        text = method(item)
        self._text += self._indentText(text)
        self._identifierStack.append("gsubSubtable")

    def _writeGSUBSubtableType1(self, item):
        target = item["target"][0]
        substitution = item["substitution"][0]
        text = [
            "sub %s by %s;" % (self._flattenItem(target), self._flattenItem(substitution))
        ]
        return text

    def _writeGSUBSubtableType3(self, item):
        target = item["target"][0]
        substitution = item["substitution"]
        text = [
            "sub %s from %s;" % (target, self._flattenItem(substitution))
        ]
        return text

    def _writeGSUBSubtableType4(self, item):
        target = item["target"]
        if not isinstance(target, basestring):
            target = " ".join([self._flattenItem(i) for i in target])
        substitution = item["substitution"][0]
        text = [
            "sub %s by %s;" % (target, self._flattenItem(substitution))
        ]
        return text

    def _writeGSUBSubtableType6(self, item):
        # lookahead is always a sequence
        lookahead = item["lookahead"]
        lookahead = " ".join([self._flattenItem(i) for i in lookahead])
        # backtrack is always a sequence
        backtrack = item["backtrack"]
        backtrack = " ".join([self._flattenItem(i) for i in backtrack])
        # target is always a sequence
        target = item["target"]
        target = " ".join([self._flattenItem(i) + "'" for i in target])
        # substitution is either a sequence or nothing
        substitution = item["substitution"]
        isIgnore = False
        if not substitution:
            isIgnore = True
        else:
            substitution = " ".join([self._flattenItem(i) for i in substitution])
        # write
        text = []
        if isIgnore:
            text += ["ignore sub"]
        else:
            text += ["sub"]
        if backtrack:
            text += [backtrack]
        text += [target]
        if lookahead:
            text += [lookahead]
        if not isIgnore:
            text += ["by"] + [substitution]
        text = " ".join(text) + ";"
        text = [
            text
        ]
        return text

    # GPOS

    def gposSubtable(self, target, positioning, backtrack=[], lookahead=[], type=None):
        raise NotImplementedError
