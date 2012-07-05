from abstractWriter import AbstractWriter


defaultLookupFlag = dict(
    rightToLeft=False,
    ignoreBaseGlyphs=False,
    ignoreLigatures=False,
    ignoreMarks=False,
    markAttachmentType=False
)


needSpaceBefore = "addFeature addLookup addScript addLanguage setLookupReference".split(" ")
needSpaceAfter = "addFeature addLookup addScript addLanguage setLookupReference".split(" ")


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
        # reset the indents
        self._inScript = False
        self._inLanguage = False
        # write
        for item in self._content:
            kwargs = dict(item)
            identifier = kwargs.pop("identifier")
            if identifier in ("addFeature", "addLookup"):
                # set the indent level based on the current scope
                writer = kwargs["writer"]
                if identifier == "addFeature":
                    writer._indent = self._indentLevel() + 1
                elif identifier == "addLookup":
                    if item["writeLookupTag"]:
                        writer._indent = self._indentLevel() + 1
                    else:
                        writer._indent = self._indentLevel()
                # if adding a feature, skim through the contents to see
                # if an initial lookup container is needed
                if identifier == "addFeature":
                    subLookups = []
                    for otherItem in writer._content:
                        if otherItem["identifier"] == "addLookup":
                            subLookups.append(otherItem)
                    if len(subLookups) == 1:
                        otherItem = subLookups[-1]
                        otherItem["writeLookupTag"] = False
                writer._preWrite()
            methodName = "_" + identifier
            method = getattr(self, methodName)
            method(**kwargs)

    # white space

    def _handleBreakBefore(self, identifier):
        # always need break
        if identifier in needSpaceBefore:
            self._text.append("")
            # need two empty lines
            if self._indent == 0 and identifier in ("addFeature", "addLookup"):
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

    def _flattenClass(self, members):
        if len(members) == 1:
            return members[0]
        return "[%s]" % " ".join(members)

    def _flattenSequence(self, members):
        members = [self._flattenClass(i) for i in members]
        return " ".join(members)

    # ---------
    # Filtering
    # ---------

    def _filterContent(self):
        self._newContent = []
        while self._content:
            item = self._content.pop(0)
            identifier = item["identifier"]
            # script
            if identifier == "addScript":
                item = self._filterScript(item)
            # language
            elif identifier == "addLanguage":
                item = self._filterLanguage(item)
            # lookup flag
            elif identifier == "addLookupFlag":
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
                    if identifier.startswith("addLookup"):
                        needScript = True
                    # subtable
                    elif identifier == "addGSUBSubtable":
                        needScript = True
                    elif identifier == "addGPOSSubtable":
                        needScript = True
                break
            # don't write the script if no lookups or subtables are
            # between this script and the end of the scope
            # or another script declaration.
            else:
                for otherItem in self._content:
                    identifier = otherItem["identifier"]
                    # lookup or lookup reference
                    if identifier.startswith("addLookup"):
                        needScript = True
                    # subtable
                    elif identifier == "addGSUBSubtable":
                        needScript = True
                    elif identifier == "addGPOSSubtable":
                        needScript = True
                    # script
                    elif identifier == "addScript":
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
                    if identifier == "addScript":
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
                    if identifier.startswith("addLookup"):
                        needLanguage = True
                    # subtable
                    elif identifier == "addGSUBSubtable":
                        needLanguage = True
                    elif identifier == "addGPOSSubtable":
                        needLanguage = True
                    # script
                    elif identifier == "addScript":
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

    def addFileReference(self, path):
        # don't filter
        if not self._filter:
            self._addFileReference(path)
            return
        # filter
        d = dict(
            identifier="addFileReference",
            path=path
        )
        self._content.append(d)

    def _addFileReference(self, path):
        self._handleBreakBefore("addFileReference")
        text = [
            "include(%s);" % path
        ]
        self._text += self._indentText(text)
        self._identifierStack.append("addFileReference")

    # language system

    def addLanguageSystem(self, script, language):
        # don't filter
        if not self._filter:
            self._addLanguageSystem(script, language)
            return
        # filter
        d = dict(
            identifier="addLanguageSystem",
            script=script,
            language=language
        )
        self._content.append(d)

    def _addLanguageSystem(self, script, language):
        if language is None:
            language = "dflt"
        language = language.strip()
        self._handleBreakBefore("addLanguageSystem")
        text = [
            "languagesystem %s %s;" % (script, language)
        ]
        self._text += self._indentText(text)
        self._identifierStack.append("addLanguageSystem")

    # script

    def addScript(self, name):
        # don't filter
        if not self._filter:
            self._addScript(name)
            return
        # filter
        d = dict(
            identifier="addScript",
            name=name
        )
        self._content.append(d)
        # shift the indents
        self._inScript = True
        self._inLanguage = False

    def _addScript(self, name):
        # shift the indents back
        self._inScript = False
        self._inLanguage = False
        # write
        self._handleBreakBefore("addScript")
        text = [
            "script %s;" % name
        ]
        self._text += self._indentText(text)
        # shift the following lines
        self._inScript = True
        # done
        self._identifierStack.append("addScript")

    # language

    def addLanguage(self, name, includeDefault=True):
        # don't filter
        if not self._filter:
            self._addLanguage(name, includeDefault)
            return
        # filter
        d = dict(
            identifier="addLanguage",
            name=name,
            includeDefault=includeDefault
        )
        self._content.append(d)
        # shift the indents
        self._inLanguage = True

    def _addLanguage(self, name, includeDefault=True):
        # shift the indent back
        self._inLanguage = False
        # write
        if name is None:
            name = "dflt"
        name = name.strip()
        self._handleBreakBefore("addLanguage")
        text = [
            "language %s;" % name
        ]
        self._text += self._indentText(text)
        # shift the following lines
        self._inLanguage = True
        # done
        self._identifierStack.append("addLanguage")

    # class definitiion

    def addClassDefinition(self, name, members):
        # don't filter
        if not self._filter:
            self._addClassDefinition(name, members)
            return
        # filter
        d = dict(
            identifier="addClassDefinition",
            name=name,
            members=members
        )
        self._content.append(d)

    def _addClassDefinition(self, name, members):
        self._handleBreakBefore("addClassDefinition")
        text = [
            "%s = %s;" % (name, self._flattenClass(members))
        ]
        self._text += self._indentText(text)
        self._identifierStack.append("addClassDefinition")

    # feature

    def addFeature(self, name):
        writer = self.__class__(whitespace=self._whitespace, filterRedundancies=self._filter)
        writer._indent = self._indent + 1
        # don't filter
        if not self._filter:
            self._addFeature(name, writer)
            return writer
        # filter
        d = dict(
            identifier="addFeature",
            name=name,
            writer=writer
        )
        self._content.append(d)
        return writer

    def _addFeature(self, name, writer):
        self._handleBreakBefore("addFeature")
        # start
        s = "feature %s {" % name
        self._text += self._indentText([s])
        # store the new writer
        self._text.append(writer)
        # close
        s = "} %s;" % name
        self._text += self._indentText([s])
        self._identifierStack.append("addFeature")

    # lookup

    def addLookup(self, name):
        writer = self.__class__(whitespace=self._whitespace, filterRedundancies=self._filter)
        writer._indent = self._indentLevel() + 1
        # don't filter
        if not self._filter:
            self._addLookup(name, writer, True)
            return writer
        # filter
        writer._initialLookupFlag = self._findCurrentLookupFlag(self._content)
        d = dict(
            identifier="addLookup",
            name=name,
            writer=writer,
            writeLookupTag=True
        )
        self._content.append(d)
        return writer

    def _addLookup(self, name, writer, writeLookupTag):
        if writeLookupTag:
            self._handleBreakBefore("addLookup")
            # start
            s = "lookup %s {" % name
            self._text += self._indentText([s])
        # store the new writer
        self._text.append(writer)
        # close
        if writeLookupTag:
            s = "} %s;" % name
            self._text += self._indentText([s])
            self._identifierStack.append("addLookup")
        return writer

    # lookup flag

    def _findCurrentLookupFlag(self, content):
        for item in reversed(content):
            identifier = item["identifier"]
            if identifier == "addLookupFlag":
                d = dict(item)
                del d["identifier"]
                return d
            elif identifier == "addScript":
                return defaultLookupFlag
        return self._initialLookupFlag

    def addLookupFlag(self, rightToLeft=False, ignoreBaseGlyphs=False, ignoreLigatures=False, ignoreMarks=False, markAttachmentType=None):
        # don't filter
        if not self._filter:
            self._addLookupFlag(rightToLeft, ignoreBaseGlyphs, ignoreLigatures, ignoreMarks, markAttachmentType)
            return
        # filter
        d = dict(
            identifier="addLookupFlag",
            rightToLeft=rightToLeft,
            ignoreBaseGlyphs=ignoreBaseGlyphs,
            ignoreLigatures=ignoreLigatures,
            ignoreMarks=ignoreMarks,
            markAttachmentType=markAttachmentType
        )
        self._content.append(d)

    def _addLookupFlag(self, rightToLeft=False, ignoreBaseGlyphs=False, ignoreLigatures=False, ignoreMarks=False, markAttachmentType=None):
        self._handleBreakBefore("addLookupFlag")
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
        self._identifierStack.append("addLookupFlag")

    # feature reference

    def addFeatureReference(self, name):
        # don't filter
        if not self._filter:
            self._addFeatureReference(name)
            return
        # filter
        d = dict(
            identifier="addFeatureReference",
            name=name
        )
        self._content.append(d)

    def _addFeatureReference(self, name):
        raise NotImplementedError

    # lookup reference

    def addLookupReference(self, name):
        # don't filter
        if not self._filter:
            self._addLookupReference(name)
            return
        # filter
        d = dict(
            identifier="addLookupReference",
            name=name
        )
        self._content.append(d)

    def _addLookupReference(self, name):
        self._handleBreakBefore("addLookupReference")
        text = [
            "lookup %s;" % name
        ]
        self._text += self._indentText(text)
        self._identifierStack.append("addLookupReference")

    # GSUB

    def addGSUBSubtable(self, target, substitution, type, backtrack=[], lookahead=[]):
        assert isinstance(target, list)
        assert isinstance(substitution, list)
        assert isinstance(backtrack, list)
        assert isinstance(lookahead, list)
        # don't filter
        if not self._filter:
            self._addGSUBSubtable(target, substitution, type, backtrack, lookahead)
            return
        # filter
        d = dict(
            identifier="addGSUBSubtable",
            type=type,
            target=target,
            substitution=substitution,
            backtrack=backtrack,
            lookahead=lookahead
        )
        self._content.append(d)

    def _addGSUBSubtable(self, target, substitution, type, backtrack=[], lookahead=[]):
        self._handleBreakBefore("addGSUBSubtable")
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
        self._identifierStack.append("addGSUBSubtable")

    def _writeGSUBSubtableGeneric(self, item):
        text = []
        for index, target in enumerate(item["target"]):
            target = self._flattenSequence(target)
            substitution = item["substitution"][index]
            substitution = self._flattenSequence(substitution)
            t = "sub %s by %s;" % (target, substitution)
            text.append(t)
        return text

    _writeGSUBSubtableType1 = _writeGSUBSubtableGeneric

    def _writeGSUBSubtableType3(self, item):
        text = []
        for index, target in enumerate(item["target"]):
            target = self._flattenSequence(target)
            substitution = item["substitution"][index]
            substitution = self._flattenSequence(substitution)
            t = "sub %s from [%s];" % (target, substitution)
            text.append(t)
        return text

    _writeGSUBSubtableType4 = _writeGSUBSubtableGeneric

    def _writeGSUBSubtableType6(self, item):
        text = []
        lookahead = item["lookahead"]
        lookahead = self._flattenSequence(lookahead)
        backtrack = item["backtrack"]
        backtrack = self._flattenSequence(backtrack)
        for index, target in enumerate(item["target"]):
            newTarget = []
            for member in target:
                member = self._flattenClass(member) + "'"
                newTarget.append(member)
            target = " ".join(newTarget)
            substitution = item["substitution"]
            isIgnore = False
            if not substitution:
                isIgnore = True
            else:
                substitution = self._flattenSequence(substitution[index])
            t = []
            if isIgnore:
                t += ["ignore sub"]
            else:
                t += ["sub"]
            if backtrack:
                t += [backtrack]
            t += [target]
            if lookahead:
                t += [lookahead]
            if not isIgnore:
                t += ["by"] + [substitution]
            t = " ".join(t) + ";"
            text.append(t)
        return text

    # GPOS

    def addGPOSSubtable(self, target, positioning, backtrack=[], lookahead=[], type=None):
        raise NotImplementedError
