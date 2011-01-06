from feaTools2 import FeaToolsError


class Tables(object):

    def __init__(self):
        self._gsub = Table()
        self._gsub.tag = "GSUB"
        self._gpos = Table()
        self._gpos.tag = "GPOS"

    def __getitem__(self, key):
        if key == "GSUB":
            return self._gsub
        if key == "GPOS":
            return self._gpos
        raise KeyError, "Unknonw table %s." % key


class Table(list):

    def __init__(self):
        self.tag = None
        self.classes = Classes()
        self.lookups = []

    # writing

    def write(self, writer):
        # language systems
        languageSystems = set()
        for feature in self:
            for script in feature.scripts:
                scriptTag = script.tag
                if scriptTag == "DFLT":
                    scriptTag = None
                for language in script.languages:
                    languageTag = language.tag
                    languageSystems.add((scriptTag, languageTag))
        for scriptTag, languageTag in sorted(languageSystems):
            if scriptTag is None:
                scriptTag = "DFLT"
            writer.addLanguageSystem(scriptTag, languageTag)
        # classes
        for name, members in sorted(self.classes.items()):
            writer.addClassDefinition(name, members)
        # lookups
        for lookup in self.lookups:
            lookupWriter = writer.addLookup(lookup.name)
            lookup.write(lookupWriter)
        # features
        for feature in self:
            featureWriter = writer.addFeature(feature.tag)
            feature.write(featureWriter)

    # manipulation

    def removeGlyphs(self, glyphNames):
        self.classes.removeGlyphs(glyphNames)
        for lookup in self.lookups:
            lookup.removeGlyphs(glyphNames)
        for feature in self:
            feature.removeGlyphs(glyphNames)

    def renameGlyphs(self, glyphMapping):
        self.classes.renameGlyphs(glyphMapping)
        for lookup in self.lookups:
            lookup.renameGlyphs(glyphMapping)
        for feature in self:
            feature.renameGlyphs(glyphMapping)

    def cleanup(self):
        # remove empty classes
        removedClasses = set()
        for name, members in self.classes.items():
            if not members:
                removedClasses.add(name)
                del self.classes[name]
        # remove empty lookups
        removedLookups = set()
        newLookups = []
        for lookup in self.lookups:
            # remove the classes
            lookup._removeClassReferences(removedClasses)
            # clean up
            lookup.cleanup()
            # flag for removal
            if lookup._shouldBeRemoved():
                removedLookups.add(lookup.name)
            else:
                newLookups.append(lookup)
        self.lookups = newLookups
        # handle the features
        toRemove = []
        for index, feature in enumerate(self):
            # remove the classes
            feature._removeClassReferences(removedClasses)
            # remove the lookups
            feature._removeLookupReferences(removedLookups)
            # clean up
            feature.cleanup()
            # flag for removal
            if feature._shouldBeRemoved():
                toRemove.append(index)
        # remove
        for index in reversed(toRemove):
            del self[index]

    # writer API

    def addLanguageSystem(self, script, language):
        # this has no meaning here
        pass

    def addClassDefinition(self, name, members):
        self.classes[name] = Class(members)

    def addFeature(self, name):
        feature = Feature()
        feature.tag = name
        self.append(feature)
        return feature

    def addLookup(self, name):
        lookup = Lookup()
        lookup.name = name
        self.lookups.append(lookup)
        return lookup

    # compression

    def compress(self):
        self._compressLookups()
        self._compressClasses()

    def _compressLookups(self):
        """
        Locate lookups that occur in more than one feature.
        These can be promoted to global lookups.
        """
        # find all potential lookups
        lookupOrder = []
        candidates = {}
        for feature in self:
            lookups = feature._findLookups()
            for lookup in lookups:
                if lookup not in lookupOrder:
                    lookupOrder.append(lookup)
                if lookup not in candidates:
                    candidates[lookup] = set()
                candidates[lookup].add(feature.tag)
        # store all lookups that occur in > 1 features
        usedNames = set()
        lookups = {}
        for lookup in lookupOrder:
            features = candidates[lookup]
            if len(features) == 1:
                continue
            lookupName = nameLookup(features)
            counter = 1
            while 1:
                name = lookupName + "_" + str(counter)
                counter += 1
                if name not in usedNames:
                    lookupName = name
                    usedNames.add(lookupName)
                    break
            lookups[lookupName] = lookup
        for name, lookup in sorted(lookups.items()):
            self.lookups.append(lookup)
        # populate global lookups
        flippedLookups = {}
        for k, v in lookups.items():
            flippedLookups[v] = k
        for feature in self:
            feature._populateGlobalLookups(flippedLookups)
        # name the global lookups
        # this can't be done earlier because it
        # will throw off the == comparison when
        # trying to find duplicate lookups
        for name, lookup in lookups.items():
            lookup.name = name
        # compress feature level lookups
        for feature in self:
            feature._compressLookups()

    def _compressClasses(self):
        # find all potential classes
        classOrder = []
        potentialClasses = {}
        for feature in self:
            candidates = feature._findPotentialClasses()
            for candidate in candidates:
                if candidate not in potentialClasses:
                    potentialClasses[candidate] = []
                    classOrder.append(candidate)
                potentialClasses[candidate].append(feature.tag)
        # name the classes
        usedNames = set()
        classes = {}
        featureClasses = {}
        for members in classOrder:
            features = potentialClasses[members]
            className = nameClass(features, members)
            counter = 1
            while 1:
                name = className + "_" + str(counter)
                counter += 1
                if name not in usedNames:
                    className = name
                    usedNames.add(className)
                    break
            classes[members] = className
            if len(features) > 1:
                self.classes[className] = Class(members)
            else:
                feature = features[0]
                if feature not in featureClasses:
                    featureClasses[feature] = {}
                featureClasses[feature][className] = members
        # populate the classes
        for feature in self:
            feature._populateClasses(classes, featureClasses.get(feature.tag, {}))


class Feature(object):

    def __init__(self):
        self.tag = None
        self.classes = Classes()
        self.scripts = []

    # writing

    def write(self, writer):
        # classes
        for name, members in sorted(self.classes.items()):
            writer.addClassDefinition(name, members)
        # scripts
        for script in self.scripts:
            script.write(writer)

    # writer API

    def addClassDefinition(self, name, members):
        self.classes[name] = Class(members)

    def addScript(self, name):
        # prevent direct duplication
        if not self.scripts or self.scripts[-1].tag != name:
            script = Script()
            script.tag = name
            self.scripts.append(script)

    def addLanguage(self, name, includeDefault=True):
        if not self.scripts:
            raise FeaToolsError, "A script must be defined before adding a language."
        self.scripts[-1].addLanguage(name, includeDefault=includeDefault)

    def addLookup(self, name):
        if not self.scripts:
            raise FeaToolsError, "A script must be defined before adding a lookup."
        if not self.scripts[-1].languages:
            raise FeaToolsError, "A language must be defined before adding a lookup."
        return self.scripts[-1].languages[-1].addLookup(name)

    def addLookupReference(self, name):
        if not self.scripts:
            raise FeaToolsError, "A script must be defined before adding a lookup reference."
        if not self.scripts[-1].languages:
            raise FeaToolsError, "A language must be defined before adding a lookup reference."
        self.scripts[-1].languages[-1].addLookupReference(name)

    # manipulation

    def removeGlyphs(self, glyphNames):
        self.classes.removeGlyphs(glyphNames)
        for script in self.scripts:
            script.removeGlyphs(glyphNames)

    def renameGlyphs(self, glyphMapping):
        self.classes.renameGlyphs(glyphMapping)
        for script in self.scripts:
            script.renameGlyphs(glyphMapping)

    def cleanup(self):
        # remove empty local classes
        removedClasses = set()
        for name, members in self.classes.items():
            if not members:
                removedClasses.add(name)
                del self.classes[name]
        # handle the script
        toRemove = []
        for index, script in enumerate(self.scripts):
            # remove class references
            script._removeClassReferences(removedClasses)
            # clean up
            script.cleanup()
            # flag it for removal
            if script._shouldBeRemoved():
                toRemove.append(index)
        # remove scripts
        for index in reversed(toRemove):
            del self.scripts[index]

    def _removeClassReferences(self, removedClasses):
        for script in self.scripts:
            script._removeClassReferences(removedClasses)

    def _removeLookupReferences(self, removedLookups):
        for script in self.scripts:
            script._removeLookupReferences(removedLookups)

    def _shouldBeRemoved(self):
        for script in self.scripts:
            if not script._shouldBeRemoved():
                return False
        return True

    # compress lookups

    def _findLookups(self):
        lookups = []
        for script in self.scripts:
            for lookup in script._findLookups():
                if lookup not in lookups:
                    lookups.append(lookup)
        return lookups

    def _populateGlobalLookups(self, flippedLookups):
        for script in self.scripts:
            script._populateGlobalLookups(flippedLookups)

    def _compressLookups(self):
        self._compressFeatureLookups()
        self._compressDefaultLookups()

    def _compressFeatureLookups(self):
        # find
        lookups = {}
        counter = 1
        for lookup in self._findLookups():
            lookupName = nameLookup([self.tag]) + "_" + str(counter)
            lookups[lookup] = lookupName
            counter += 1
        # populate
        haveSeen = dict.fromkeys(lookups.values(), False)
        for script in self.scripts:
            script._populateFeatureLookups(lookups, haveSeen)
        # name
        for lookup, name in lookups.items():
            lookup.name = name

    def _compressDefaultLookups(self):
        # group the lookups based on script and language
        defaultLookups = []
        scriptDefaultLookups = {}
        languageSpecificLookups = {}
        for script in self.scripts:
            for language in script.languages:
                # check to make sure that the default hasn't happened twice
                if script.tag == "DFLT" and language.tag is None:
                    pass
                elif language.tag is None:
                    assert script.tag not in scriptDefaultLookups, "Default language appears more than once."
                    scriptDefaultLookups[script.tag] = (language, [])
                else:
                    assert (script.tag, language.tag) not in languageSpecificLookups, "Script+language combo appears more than once"
                    languageSpecificLookups[script.tag, language.tag] = (language, [])
                # store the lookups
                for lookup in language.lookups:
                    if script.tag == "DFLT" and language.tag is None:
                        defaultLookups.append(lookup)
                    elif language.tag is None:
                        scriptDefaultLookups[script.tag][1].append(lookup)
                    else:
                        languageSpecificLookups[script.tag, language.tag][1].append((lookup))
        # clear out redundant lookups from scripts
        for scriptTag, (language, lookups) in scriptDefaultLookups.items():
            # compare and slice as necessary
            newLookups = []
            for index, lookup in enumerate(lookups):
                if index >= len(defaultLookups) or lookup.name != defaultLookups[index].name:
                    newLookups += lookups[index:]
                    break
            language.lookups = newLookups
            scriptDefaultLookups[scriptTag] = (language, newLookups)
        # clear out redundant lookups from languages
        for (scriptTag, languageTag), (language, lookups) in languageSpecificLookups.items():
            # create a default comparable
            defaultLookupNames = [lookup.name for lookup in defaultLookups]
            scriptData = scriptDefaultLookups.get(scriptTag)
            if scriptData:
                script, scriptLookups = scriptData
                defaultLookupNames += [lookup.name for lookup in scriptLookups]
            # create a comparable for this language
            languageLookupNames = [lookup.name for lookup in lookups]
            # compare
            includeDefault = True
            if len(defaultLookupNames) > len(languageLookupNames):
                includeDefault = False
            else:
                languageSlice = languageLookupNames[:len(defaultLookupNames)]
                if languageSlice != defaultLookupNames:
                    includeDefault = False
            # adjust
            if not includeDefault:
                language.includeDefault = False
            else:
                language.lookups = language.lookups[len(defaultLookupNames):]

    # compress classes

    def _findPotentialClasses(self):
        candidates = []
        for script in self.scripts:
            for candidate in script._findPotentialClasses():
                if candidate not in candidates:
                    candidates.append(candidate)
        return candidates

    def _populateClasses(self, allClasses, featureClasses):
        new = {}
        for name, members in featureClasses.items():
            new[name] = Class(members)
        self.classes.update(new)
        for script in self.scripts:
            script._populateClasses(allClasses)


class Script(object):

    def __init__(self):
        self.tag = None
        self.languages = []

    # writing

    def write(self, writer):
        writer.addScript(self.tag)
        # languages
        for language in self.languages:
            language.write(writer)

    # writer API

    def addLanguage(self, name, includeDefault=True):
        # prevent direct duplication
        if not self.languages or self.languages[-1].tag != name:
            language = Language()
            language.tag = name
            language.includeDefault = includeDefault
            self.languages.append(language)

    # manipulation

    def removeGlyphs(self, glyphNames):
        for language in self.languages:
            language.removeGlyphs(glyphNames)

    def renameGlyphs(self, glyphMapping):
        for language in self.languages:
            language.renameGlyphs(glyphMapping)

    def cleanup(self):
        # handle the languages
        toRemove = []
        for index, language in enumerate(self.languages):
            # clean up
            language.cleanup()
            # flag it for removal
            if language._shouldBeRemoved():
                toRemove.append(index)
        # remove scripts
        for index in reversed(toRemove):
            del self.languages[index]

    def _removeClassReferences(self, removedClasses):
        for language in self.languages:
            language._removeClassReferences(removedClasses)

    def _removeLookupReferences(self, removedLookups):
        for language in self.languages:
            language._removeLookupReferences(removedLookups)

    def _shouldBeRemoved(self):
        for language in self.languages:
            if not language._shouldBeRemoved():
                return False
        return True

    # compression

    def _findLookups(self):
        lookups = []
        for language in self.languages:
            for lookup in language.lookups:
                if isinstance(lookup, LookupReference):
                    continue
                if lookup not in lookups:
                    lookups.append(lookup)
        return lookups

    def _populateGlobalLookups(self, flippedLookups):
        for language in self.languages:
            language._populateGlobalLookups(flippedLookups)

    def _populateFeatureLookups(self, flippedLookups, haveSeen):
        for language in self.languages:
            language._populateFeatureLookups(flippedLookups, haveSeen)

    def _findPotentialClasses(self):
        candidates = []
        for language in self.languages:
            for candidate in language._findPotentialClasses():
                if candidate not in candidates:
                    candidates.append(candidate)
        return candidates

    def _populateClasses(self, classes):
        for language in self.languages:
            language._populateClasses(classes)


class Language(object):

    def __init__(self):
        self.tag = None
        self.includeDefault = True
        self.lookups = []

    # writing

    def write(self, writer):
        writer.addLanguage(self.tag, includeDefault=self.includeDefault)
        # lookups
        for lookup in self.lookups:
            if isinstance(lookup, LookupReference):
                writer.addLookupReference(lookup.name)
            else:
                lookupWriter = writer.addLookup(lookup.name)
                lookup.write(lookupWriter)

    # writer API

    def addLookup(self, name):
        lookup = Lookup()
        lookup.name = name
        self.lookups.append(lookup)
        return lookup

    def addLookupReference(self, name):
        lookupReference = LookupReference()
        lookupReference.name = name
        self.lookups.append(lookupReference)

    # manipulation

    def removeGlyphs(self, glyphNames):
        for lookup in self.lookups:
            if isinstance(lookup, LookupReference):
                continue
            lookup.removeGlyphs(glyphNames)

    def renameGlyphs(self, glyphMapping):
        for lookup in self.lookups:
            if isinstance(lookup, LookupReference):
                continue
            lookup.renameGlyphs(glyphMapping)

    def cleanup(self):
        # handle the lookups
        toRemove = []
        for index, lookup in enumerate(self.lookups):
            if isinstance(lookup, LookupReference):
                continue
            # clean up
            lookup.cleanup()
            # flag it for removal
            if lookup._shouldBeRemoved():
                toRemove.append(index)
        # remove scripts
        for index in reversed(toRemove):
            del self.lookups[index]

    def _removeClassReferences(self, removedClasses):
        for lookup in self.lookups:
            if isinstance(lookup, LookupReference):
                continue
            lookup._removeClassReferences(removedClasses)

    def _removeLookupReferences(self, removedLookups):
        toRemove = []
        for index, lookup in enumerate(self.lookups):
            if isinstance(lookup, LookupReference) and lookup.name in removedLookups:
                toRemove.append(index)
        for index in reversed(toRemove):
            del self.lookups[index]

    def _shouldBeRemoved(self):
        for lookup in self.lookups:
            if isinstance(lookup, LookupReference):
                return False
            if not lookup._shouldBeRemoved():
                return False
        return True

    # compress lookups

    def _populateGlobalLookups(self, flippedLookups):
        lookups = []
        for lookup in self.lookups:
            if lookup in flippedLookups:
                lookupName = flippedLookups[lookup]
                lookup = LookupReference()
                lookup.name = lookupName
            lookups.append(lookup)
        self.lookups = lookups

    def _populateFeatureLookups(self, flippedLookups, haveSeen):
        lookups = []
        for lookup in self.lookups:
            if isinstance(lookup, LookupReference):
                pass
            elif lookup in flippedLookups:
                lookupName = flippedLookups[lookup]
                if haveSeen[lookupName]:
                    lookup = LookupReference()
                    lookup.name = lookupName
                else:
                    haveSeen[lookupName] = True
            lookups.append(lookup)
        self.lookups = lookups

    # compress classes

    def _findPotentialClasses(self):
        candidates = []
        for lookup in self.lookups:
            if isinstance(lookup, LookupReference):
                continue
            for candidate in lookup._findPotentialClasses():
                if candidate not in candidates:
                    candidates.append(candidate)
        return candidates

    def _populateClasses(self, classes):
        for lookup in self.lookups:
            if isinstance(lookup, LookupReference):
                continue
            lookup._populateClasses(classes)


class Lookup(object):

    def __init__(self):
        self.name = None
        self.flag = LookupFlag()
        self.subtables = []

    # writing

    def write(self, writer):
        # lookup flag
        self.flag.write(writer)
        # subtables
        for subtable in self.subtables:
            subtable.write(writer)

    # writer API

    def addLookupFlag(self, rightToLeft=False, ignoreBaseGlyphs=False, ignoreLigatures=False, ignoreMarks=False, markAttachmentType=None):
        lookupFlag = LookupFlag()
        lookupFlag.rightToLeft = rightToLeft
        lookupFlag.ignoreBaseGlyphs = ignoreBaseGlyphs
        lookupFlag.ignoreLigatures = ignoreLigatures
        lookupFlag.ignoreMarks = ignoreMarks
        lookupFlag.markAttachmentType = markAttachmentType
        self.flag = lookupFlag

    def _convertSequence(self, sequence):
        newSequence = Sequence()
        for group in sequence:
            newGroup = Class()
            for member in group:
                if member.startswith("@"):
                    m = ClassReference()
                    m.name = member
                    member = m
                newGroup.append(member)
            newSequence.append(newGroup)
        return newSequence

    def addGSUBSubtable(self, target, substitution, type, backtrack=[], lookahead=[]):
        subtable = GSUBSubtable()
        subtable.type = type
        subtable.target = [self._convertSequence(i) for i in target]
        subtable.substitution = [self._convertSequence(i) for i in substitution]
        subtable.backtrack = self._convertSequence(backtrack)
        subtable.lookahead = self._convertSequence(lookahead)
        self.subtables.append(subtable)

    def addGPOSSubtable(self, target, positioning, backtrack=[], lookahead=[], type=None):
        raise NotImplementedError

    def addFeatureReference(self, name):
        raise NotImplementedError

    # manipulation

    def removeGlyphs(self, glyphNames):
        for subtable in self.subtables:
            subtable.removeGlyphs(glyphNames)

    def renameGlyphs(self, glyphMapping):
        for subtable in self.subtables:
            subtable.renameGlyphs(glyphMapping)

    def cleanup(self):
        # handle the subtables
        toRemove = []
        for index, subtable in enumerate(self.subtables):
            # clean up
            subtable.cleanup()
            # flag it for removal
            if subtable._shouldBeRemoved():
                toRemove.append(index)
        # remove scripts
        for index in reversed(toRemove):
            del self.subtables[index]

    def _removeClassReferences(self, removedClasses):
        for subtable in self.subtables:
            subtable._removeClassReferences(removedClasses)

    def _shouldBeRemoved(self):
        for subtable in self.subtables:
            if not subtable._shouldBeRemoved():
                return False
        return True

    # compression

    def _findPotentialClasses(self):
        candidates = []
        for subtable in self.subtables:
            for candidate in subtable._findPotentialClasses():
                if candidate not in candidates:
                    candidates.append(candidate)
        return candidates

    def _populateClasses(self, classes):
        for subtable in self.subtables:
            subtable._populateClasses(classes)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.flag != other.flag:
            return False
        if self.subtables != other.subtables:
            return False
        return True

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        s = "Lookup | name=%s flag=%s subtables=%s" % (
            self.name,
            str(hash(self.flag)),
            " ".join([str(hash(i)) for i in self.subtables])
        )
        return hash(s)


class LookupReference(object):

    def __init__(self):
        self.name = None

    def write(self, writer):
        writer.addLookupReference(self.name)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.name == other.name

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        s = "LookupReference | name=%s" % self.name
        return hash(s)


class LookupFlag(object):

    def __init__(self):
        self.rightToLeft = False
        self.ignoreBaseGlyphs = False
        self.ignoreLigatures = False
        self.ignoreMarks = False
        self.markAttachmentType = False

    def write(self, writer):
        writer.addLookupFlag(
            rightToLeft=self.rightToLeft,
            ignoreBaseGlyphs=self.ignoreBaseGlyphs,
            ignoreLigatures=self.ignoreLigatures,
            ignoreMarks=self.ignoreMarks,
            markAttachmentType=self.markAttachmentType
        )

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.rightToLeft != other.rightToLeft:
            return False
        if self.ignoreBaseGlyphs != other.ignoreBaseGlyphs:
            return False
        if self.ignoreLigatures != other.ignoreLigatures:
            return False
        if self.ignoreMarks != other.ignoreMarks:
            return False
        if self.markAttachmentType != other.markAttachmentType:
            return False
        return True

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        s = "LookupFlag | rightToLeft=%s ignoreBaseGlyphs=%s ignoreLigatures=%s ignoreMarks=%s markAttachmentType=%s" % (
            self.rightToLeft,
            self.ignoreBaseGlyphs,
            self.ignoreLigatures,
            self.ignoreMarks,
            self.markAttachmentType
        )
        return hash(s)


class GSUBSubtable(object):

    def __init__(self):
        self.type = None
        self._backtrack = Sequence()
        self._lookahead = Sequence()
        self._target = Sequence()
        self._substitution = Sequence()
        self._manipulationResultedInEmptySubstitution = False

    # attribute setting

    def _get_backtrack(self):
        return self._backtrack

    def _set_backtrack(self, value):
        self._backtrack = Sequence(value)

    backtrack = property(_get_backtrack, _set_backtrack)

    def _get_lookahead(self):
        return self._lookahead

    def _set_lookahead(self, value):
        self._lookahead = Sequence(value)

    lookahead = property(_get_lookahead, _set_lookahead)

    def _get_target(self):
        return self._target

    def _set_target(self, value):
        self._target = value

    target = property(_get_target, _set_target)

    def _get_substitution(self):
        return self._substitution

    def _set_substitution(self, value):
        # any setting of the value causes the flag
        # as a result of a manipulation to go away
        self._manipulationResultedInEmptySubstitution = False
        self._substitution = value

    substitution = property(_get_substitution, _set_substitution)

    # write

    def write(self, writer):
        target = [self._flattenClassReferences(i) for i in self.target]
        substitution = [self._flattenClassReferences(i) for i in self.substitution]
        backtrack = self._flattenClassReferences(self.backtrack)
        lookahead = self._flattenClassReferences(self.lookahead)
        writer.addGSUBSubtable(target, substitution, self.type, backtrack=backtrack, lookahead=lookahead)

    def _flattenClassReferences(self, sequence):
        newSequence = []
        for group in sequence:
            newGroup = Class()
            for member in group:
                if isinstance(member, ClassReference):
                    member = member.name
                newGroup.append(member)
            newSequence.append(newGroup)
        return newSequence

    # compression

    def _findPotentialClasses(self):
        candidates = []
        self._findPotentialClassesInSequence(self.backtrack, candidates)
        self._findPotentialClassesInSequence(self.lookahead, candidates)
        for sequence in self.target:
            self._findPotentialClassesInSequence(sequence, candidates)
        if self.type != 3:
            for sequence in self.substitution:
                self._findPotentialClassesInSequence(sequence, candidates)
        return candidates

    def _findPotentialClassesInSequence(self, sequence, candidates):
        for member in sequence:
            if member not in candidates:
                if len(member) > 1:
                    candidates.append(tuple(member))

    def _populateClasses(self, classes):
        self.backtrack = self._populateClassesInSequence(self.backtrack, classes)
        self.lookahead = self._populateClassesInSequence(self.lookahead, classes)
        self.target = [self._populateClassesInSequence(i, classes) for i in self.target]
        if self.type != 3:
            self.substitution = [self._populateClassesInSequence(i, classes) for i in self.substitution]

    def _populateClassesInSequence(self, sequence, classes):
        newSequence = Sequence()
        for member in sequence:
            m = tuple(member)
            if m in classes:
                classReference = ClassReference()
                classReference.name = classes[m]
                member = Class([classReference])
            newSequence.append(member)
        return newSequence

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.backtrack != other.backtrack:
            return False
        if self.lookahead != other.lookahead:
            return False
        if self.target != other.target:
            return False
        if self.substitution != other.substitution:
            return False
        return True

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        s = "GSUBSubtable | type=%d backtrack=%s lookahead=%s target=%s substitution=%s" % (
            self.type,
            " ".join([str(i) for i in self.backtrack]),
            " ".join([str(i) for i in self.lookahead]),
            " ".join([str(i) for i in self.target]),
            " ".join([str(i) for i in self.substitution])
        )
        return hash(s)

    # manipulation

    def removeGlyphs(self, glyphNames):
        self._removeGlyphsFromSequence(self.backtrack, glyphNames)
        self._removeGlyphsFromSequence(self.lookahead, glyphNames)
        for sequence in self.target:
            self._removeGlyphsFromSequence(sequence, glyphNames)
        hadSubstitution = bool(self.substitution)
        for sequence in self.substitution:
            self._removeGlyphsFromSequence(sequence, glyphNames)
        if not self.substitution and hadSubstitution:
            self._manipulationResultedInEmptySubstitution = True

    def _removeGlyphsFromSequence(self, sequence, glyphNames):
        for member in sequence:
            member.removeGlyphs(glyphNames)

    def renameGlyphs(self, glyphMapping):
        self._renameGlyphsInSequence(self.backtrack, glyphMapping)
        self._renameGlyphsInSequence(self.lookahead, glyphMapping)
        for sequence in self.target:
            self._renameGlyphsInSequence(sequence, glyphMapping)
        for sequence in self.substitution:
            self._renameGlyphsInSequence(sequence, glyphMapping)

    def _renameGlyphsInSequence(self, sequence, glyphMapping):
        for member in sequence:
            member.renameGlyphs(glyphMapping)

    def cleanup(self):
        self.backtrack.cleanup()
        self.lookahead.cleanup()
        new = []
        for sequence in self.target:
            sequence.cleanup()
            if sequence:
                new.append(sequence)
        self.target = new
        new = []
        for sequence in self.substitution:
            sequence.cleanup()
            if sequence:
                new.append(sequence)
        self.substitution = new

    def _removeClassReferences(self, removedClasses):
        self._removeClassReferencesInSequence(self.backtrack, removedClasses)
        self._removeClassReferencesInSequence(self.lookahead, removedClasses)
        for sequence in self.target:
            self._removeClassReferencesInSequence(sequence, removedClasses)
        hadSubstitution = bool(self.substitution)
        for sequence in self.substitution:
            self._removeClassReferencesInSequence(sequence, removedClasses)
        if not self.substitution and hadSubstitution:
            self._manipulationResultedInEmptySubstitution = True

    def _removeClassReferencesInSequence(self, sequence, removedClasses):
        for member in sequence:
            member._removeClassReferences(removedClasses)

    def _shouldBeRemoved(self):
        if not self.target:
            return True
        if not self.substitution and self._manipulationResultedInEmptySubstitution:
            return True
        return False


class Classes(dict):

    def removeGlyphs(self, glyphNames):
        for group in self.values():
            group.removeGlyphs(glyphNames)

    def renameGlyphs(self, glyphMapping):
        for group in self.values():
            group.renameGlyphs(glyphMapping)


class Sequence(list):

    def removeGlyphs(self, glyphNames):
        for group in self:
            group.removeGlyphs(glyphNames)

    def renameGlyphs(self, glyphMapping):
        for group in self:
            group.removeGlyphs(glyphMapping)

    def cleanup(self):
        new = []
        for group in self:
            if group:
                new.append(group)
        del self[:]
        self.extend(new)

    def _removeClassReferences(self, removedClasses):
        for group in self:
            group._removeClassReferences(removedClasses)


class Class(list):

    def removeGlyphs(self, glyphNames):
        new = [member for member in self if member not in glyphNames]
        if new != self:
            del self[:]
            self.extend(new)

    def renameGlyphs(self, glyphMapping):
        new = [glyphMapping.get(member, member) for member in self]
        if new != self:
            del self[:]
            self.extend(new)

    def _removeClassReferences(self, removedClasses):
        new = []
        for member in self:
            if isinstance(member, ClassReference) and member.name in removedClasses:
                continue
            new.append(member)
        if new != self:
            del self[:]
            self.extend(new)


class ClassReference(object):

    def __init__(self):
        self.name = None

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.name == other.name

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        s = "ClassReference | name=%s" % self.name
        return hash(s)


# ---------
# Utilities
# ---------

def nameClass(features, members):
    name = "@" + "_".join(features)
    return name

def nameLookup(features):
    return "_".join(features)
