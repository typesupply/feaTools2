class Table(list):

    def __init__(self):
        self.tag = None
        self.classes = Classes()
        self.lookups = []

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
            writer.languageSystem(scriptTag, languageTag)
        # classes
        for name, members in sorted(self.classes.items()):
            writer.classDefinition(name, members)
        # lookups
        for lookup in self.lookups:
            lookupWriter = writer.newLookup(lookup.name)
            lookup.write(lookupWriter)
        # features
        for feature in self:
            featureWriter = writer.newFeature(feature.tag)
            feature.write(featureWriter)

    def _load(self, table, tableTag):
        # first pass through the features
        features = {}
        for scriptRecord in table.ScriptList.ScriptRecord:
            scriptTag = scriptRecord.ScriptTag
            if scriptTag == "DFLT":
                scriptTag = None
            # default
            languageTag = None
            featureIndexes = scriptRecord.Script.DefaultLangSys.FeatureIndex
            for index in featureIndexes:
                featureRecord = table.FeatureList.FeatureRecord[index]
                featureTag = featureRecord.FeatureTag
                lookupIndexes = featureRecord.Feature.LookupListIndex
                if featureTag not in features:
                    features[featureTag] = []
                features[featureTag].append((scriptTag, languageTag, lookupIndexes))
            # language specific
            for languageRecord in scriptRecord.Script.LangSysRecord:
                languageTag = languageRecord.LangSysTag
                featureIndexes = languageRecord.LangSys.FeatureIndex
                for index in featureIndexes:
                    featureRecord = table.FeatureList.FeatureRecord[index]
                    featureTag = featureRecord.FeatureTag
                    lookupIndexes = featureRecord.Feature.LookupListIndex
                    if featureTag not in features:
                        features[featureTag] = []
                    features[featureTag].append((scriptTag, languageTag, lookupIndexes))
        # order the features
        sorter = []
        for featureTag, records in features.items():
            indexes = []
            for (scriptTag, languageTag, lookupIndexes) in records:
                indexes += lookupIndexes
            indexes = tuple(sorted(set(indexes)))
            sorter.append((indexes, featureTag))
        featureOrder = [featureTag for (indexes, featureTag) in sorted(sorter)]
        # sort the script and language records
        # grab the lookup records
        for featureTag, records in features.items():
            _records = []
            for (scriptTag, languageTag, lookupIndexes) in sorted(records):
                if scriptTag is None:
                    scriptTag = "DFLT"
                lookupRecords = [table.LookupList.Lookup[index] for index in lookupIndexes]
                _records.append((scriptTag, languageTag, lookupRecords))
            features[featureTag] = _records
        # do the official packing
        for featureTag in featureOrder:
            records = features[featureTag]
            feature = Feature()
            feature.tag = featureTag
            feature._load(table, tableTag, records)
            self.append(feature)
        # compress
        self._compress()

    def _compress(self):
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
        potentialClasses = {}
        for feature in self:
            candidates = feature._findPotentialClasses()
            for candidate in candidates:
                if candidate not in potentialClasses:
                    potentialClasses[candidate] = []
                potentialClasses[candidate].append(feature.tag)
        # name the classes
        usedNames = set()
        classes = {}
        featureClasses = {}
        for members, features in potentialClasses.items():
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
                self.classes[className] = members
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

    def write(self, writer):
        # classes
        for name, members in sorted(self.classes.items()):
            writer.classDefinition(name, members)
        # scripts
        for script in self.scripts:
            script.write(writer)

    # loading

    def _load(self, table, tableTag, records):
        for (scriptTag, languageTag, lookupRecords) in records:
            if self.scripts and self.scripts[-1].tag == scriptTag:
                script = self.scripts[-1]
            else:
                script = Script()
                script.tag = scriptTag
                self.scripts.append(script)
            script._load(table, tableTag, languageTag, lookupRecords)

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
        candidates = set()
        for script in self.scripts:
            candidates |= script._findPotentialClasses()
        return candidates

    def _populateClasses(self, allClasses, featureClasses):
        self.classes.update(featureClasses)
        for script in self.scripts:
            script._populateClasses(allClasses)


class Script(object):

    def __init__(self):
        self.tag = None
        self.languages = []

    def write(self, writer):
        writer.script(self.tag)
        # languages
        for language in self.languages:
            language.write(writer)

    # loading

    def _load(self, table, tableTag, languageTag, lookupRecords):
        language = Language()
        language.tag = languageTag
        language._load(table, tableTag, lookupRecords)
        self.languages.append(language)

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
        candidates = set()
        for language in self.languages:
            candidates |= language._findPotentialClasses()
        return candidates

    def _populateClasses(self, classes):
        for language in self.languages:
            language._populateClasses(classes)


class Language(object):

    def __init__(self):
        self.tag = None
        self.includeDefault = True
        self.lookups = []

    def write(self, writer):
        writer.language(self.tag, includeDefault=self.includeDefault)
        # lookups
        for lookup in self.lookups:
            if isinstance(lookup, LookupReference):
                writer.lookupReference(lookup.name)
            else:
                lookupWriter = writer.newLookup(lookup.name)
                lookup.write(lookupWriter)

    # loading

    def _load(self, table, tableTag, lookupRecords):
        for lookupRecord in lookupRecords:
            lookup = Lookup()
            lookup._load(table, tableTag, lookupRecord)
            self.lookups.append(lookup)

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
        candidates = set()
        for lookup in self.lookups:
            if isinstance(lookup, LookupReference):
                continue
            candidates |= lookup._findPotentialClasses()
        return candidates

    def _populateClasses(self, classes):
        for lookup in self.lookups:
            if isinstance(lookup, LookupReference):
                continue
            lookup._populateClasses(classes)


class Lookup(object):

    def __init__(self):
        self.name = None
        self.type = None
        self.flag = LookupFlag()
        self.subtables = []

    def write(self, writer):
        # lookup flag
        self.flag.write(writer)
        # subtables
        for subtable in self.subtables:
            subtable.write(writer)

    # loading

    def _load(self, table, tableTag, lookupRecord):
        self.type = lookupRecord.LookupType
        self.flag._load(lookupRecord.LookupFlag)
        if tableTag == "GSUB":
            subtableClass = GSUBSubtable
        else:
            raise NotImplementedError
        for subtableRecord in lookupRecord.SubTable:
            subtable = subtableClass()
            subtable._load(table, tableTag, self.type, subtableRecord)
            self.subtables.append(subtable)

    # compression

    def _findPotentialClasses(self):
        candidates = set()
        for subtable in self.subtables:
            candidates |= subtable._findPotentialClasses()
        return candidates

    def _populateClasses(self, classes):
        for subtable in self.subtables:
            subtable._populateClasses(classes)

    def __eq__(self, other):
        if self.type != other.type:
            return False
        if self.flag != other.flag:
            return False
        if self.subtables != other.subtables:
            return False
        return True

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        s = "Lookup | name=%s type=%d flag=%s subtables=%s" % (
            self.name,
            self.type,
            str(hash(self.flag)),
            " ".join([str(hash(i)) for i in self.subtables])
        )
        return hash(s)


class LookupReference(object):

    def __init__(self):
        self.name = None

    def write(self, writer):
        writer.lookupReference(self.name)

    def __eq__(self, other):
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
        writer.lookupFlag(
            rightToLeft=self.rightToLeft,
            ignoreBaseGlyphs=self.ignoreBaseGlyphs,
            ignoreLigatures=self.ignoreLigatures,
            ignoreMarks=self.ignoreMarks,
            markAttachmentType=self.markAttachmentType
        )

    def _load(self, lookupFlag):
        self.rightToLeft = bool(lookupFlag & 0x0001)
        self.ignoreBaseGlyphs = bool(lookupFlag & 0x0002)
        self.ignoreLigatures = bool(lookupFlag & 0x0004)
        self.ignoreMarks = bool(lookupFlag & 0x0008)
        self.markAttachmentType = bool(lookupFlag & 0xFF00)

    def __eq__(self, other):
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
        self._backtrack = []
        self._lookahead = []
        self._target = []
        self._substitution = []

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
        if not isinstance(value, ClassReference):
            value = Class(value)
        self._target = value

    target = property(_get_target, _set_target)

    def _get_substitution(self):
        return self._substitution

    def _set_substitution(self, value):
        if not isinstance(value, ClassReference):
            value = Class(value)
        self._substitution = value

    substitution = property(_get_substitution, _set_substitution)

    # writing

    def write(self, writer):
        if self.type == 1:
            self._writeType1(writer)
        elif self.type == 2:
            self._writeType2(writer)
        elif self.type == 3:
            self._writeType3(writer)
        elif self.type == 4:
            self._writeType4(writer)
        elif self.type == 5:
            self._writeType5(writer)
        elif self.type == 6:
            self._writeType6(writer)
        elif self.type == 7:
            self._writeType7(writer)

    def _writeType1(self, writer):
        if isinstance(self.target, ClassReference):
            target = [self.target.name]
        else:
            target = list(self.target)
        if isinstance(self.substitution, ClassReference):
            substitution = [self.substitution.name]
        else:
            substitution = list(self.substitution)
        writer.gsubSubtable([target], [substitution], self.type)

    def _writeType3(self, writer):
        for index, target in enumerate(self.target):
            target = [target]
            substitution  = self.substitution[index]
            assert isinstance(substitution, Alternates)
            writer.gsubSubtable([target], [list(substitution)], self.type)

    def _writeType4(self, writer):
        for index, target in enumerate(self.target):
            assert isinstance(target, Ligature)
            target = list(target)
            target = [[i] for i in target]
            substitution = self.substitution[index]
            assert isinstance(substitution, basestring)
            substitution = [substitution]
            writer.gsubSubtable(target, [substitution], self.type)

    def _writeType6(self, writer):
        # backtrack
        backtrack = []
        for item in self.backtrack:
            if isinstance(item, basestring):
                backtrack.append([item])
            elif isinstance(item, ClassReference):
                backtrack.append([item.name])
            elif isinstance(item, Class):
                backtrack.append(list(item))
            else:
                raise NotImplementedError, "Unknown backtrack type: %s" % repr(type(item))
        # lookahead
        lookahead = []
        for item in self.lookahead:
            if isinstance(item, basestring):
                lookahead.append([item])
            elif isinstance(item, ClassReference):
                lookahead.append([item.name])
            elif isinstance(item, Class):
                lookahead.append(list(item))
            else:
                raise NotImplementedError, "Unknown lookahead type: %s" % repr(type(item))
        # target
        if isinstance(self.target, ClassReference):
            target = [[self.target.name]]
        else:
            target = []
            for item in self.target:
                if isinstance(item, basestring):
                    target.append([item])
                elif isinstance(item, Ligature):
                    target += [[i] for i in item]
                elif isinstance(item, Class):
                    target.append(list(item))
                else:
                    raise NotImplementedError, "Unknown target type: %s" % repr(type(item))
        # substitution
        if isinstance(self.substitution, ClassReference):
            substitution = [self.substitution.name]
        else:
            substitution = []
            for item in self.substitution:
                if isinstance(item, basestring):
                    substitution.append([item])
                elif isinstance(item, Ligature):
                    substitution += [[i] for i in item]
                elif isinstance(item, Class):
                    substitution.append(list(item))
                else:
                    raise NotImplementedError, "Unknown substitution type: %s" % repr(type(item))
        writer.gsubSubtable(target, substitution, self.type, backtrack=backtrack, lookahead=lookahead)

    # loading

    def _load(self, table, tableTag, type, subtable):
        self.type = type
        if type == 1:
            self._loadType1(subtable)
        elif type == 2:
            self._loadType2(subtable)
        elif type == 3:
            self._loadType3(subtable)
        elif type == 4:
            self._loadType4(subtable)
        elif type == 5:
            self._loadType5(subtable)
        elif type == 6:
            self._loadType6(table, tableTag, subtable)
        elif type == 7:
            self._loadType7(subtable)

    def _loadType1(self, subtable):
        target = []
        substitution = []
        for t, r in sorted(subtable.mapping.items()):
            target.append(t)
            substitution.append(r)
        self.target = target
        self.substitution = substitution

    def _loadType2(self, subtable):
        raise NotImplementedError

    def _loadType3(self, subtable):
        target = []
        substitution = []
        for t, r in sorted(subtable.alternates.items()):
            target.append(t)
            substitution.append(Alternates(r))
        self.target = target
        self.substitution = substitution

    def _loadType4(self, subtable):
        target = []
        substitution = []
        for firstGlyph, parts in sorted(subtable.ligatures.items()):
            for part in parts:
                t = Ligature([firstGlyph] + part.Component)
                r = part.LigGlyph
                assert t not in target
                target.append(t)
                substitution.append(r)
        self.target = target
        self.substitution = substitution

    def _loadType5(self, subtable):
        raise NotImplementedError

    def _loadType6(self, table, tableTag, subtable):
        assert subtable.Format == 3, "Stop being lazy."
        backtrack = [readCoverage(i) for i in reversed(subtable.BacktrackCoverage)]
        lookahead = [readCoverage(i) for i in subtable.LookAheadCoverage]
        input = [readCoverage(i) for i in subtable.InputCoverage]
        target = []
        substitution = []
        # the "ignore" rule generates subtables with an empty SubstLookup
        if not subtable.SubstLookupRecord:
            target = input
            substitution = []
        else:
            assert len(subtable.SubstLookupRecord) == 1, "Does this ever happen?"
            for substLookup in subtable.SubstLookupRecord:
                index = substLookup.LookupListIndex
                lookupRecord = table.LookupList.Lookup[index]
                lookup = Lookup()
                lookup._load(table, tableTag, lookupRecord)
                # XXX potential problem here:
                # theoretically this nested lookup could have a flag that is
                # different than the flag of the lookup that contains this
                # subtable. i can't think of a way to do this with the
                # .fea syntax, so i'm not worrying about it right now.
                assert len(lookup.subtables) == 1, "Does this ever happen?"
                for index, t in enumerate(lookup.subtables[0].target):
                    if lookup.type == 1:
                        assert len(input) == 1, "Does this ever happen?"
                        if t not in input[0]:
                            continue
                    elif lookup.type == 4:
                        testTarget = [Class(i) for i in t]
                        if testTarget != input:
                            continue
                    else:
                        raise NotImplementedError
                        testTarget = Class([t])
                        if testTarget not in input:
                            continue
                    target.append(t)
                    s = lookup.subtables[0].substitution[index]
                    substitution.append(s)
        self.backtrack = backtrack
        self.lookahead = lookahead
        self.target = target
        self.substitution = substitution

    def _loadType7(self, subtable):
        pass
        #raise NotImplementedError

    # compression

    def _findPotentialClasses(self):
        if self.type in (3, 4):
            return set()
        # otherwise go ahead
        candidates = set()
        for sequence in (self.backtrack, self.lookahead):
            for candidate in sequence:
                if isinstance(candidate, Class):
                    if len(candidate) < 2:
                        continue
                    candidates.add(candidate)
        targetCandidate = True
        for member in self.target:
            if not isinstance(member, basestring):
                targetCandidate = False
                break
        if targetCandidate and len(self.target) > 1:
            candidates.add(self.target)
        substitutionCandidate = True
        if not self.substitution:
            substitutionCandidate = False
        else:
            for member in self.substitution:
                if not isinstance(member, basestring):
                    substitutionCandidate = False
                    break
        if substitutionCandidate and len(self.substitution) > 1:
            candidates.add(self.substitution)
        return candidates

    def _populateClasses(self, classes):
        if self.type in (3, 4):
            return
        # backtrack
        backtrack = []
        for member in self.backtrack:
            className = classes.get(member)
            if className is not None:
                classReference = ClassReference()
                classReference.name = className
                member = classReference
            backtrack.append(member)
        self.backtrack = backtrack
        # lookahead
        lookahead = []
        for member in self.lookahead:
            className = classes.get(member)
            if className is not None:
                classReference = ClassReference()
                classReference.name = className
                member = classReference
            lookahead.append(member)
        self.lookahead = lookahead
        # target
        if self.target in classes:
            className = classes.get(self.target)
            classReference = ClassReference()
            classReference.name = className
            self.target = classReference
        # substitution
        if self.substitution in classes:
            className = classes.get(self.substitution)
            classReference = ClassReference()
            classReference.name = className
            self.substitution = classReference

    def __eq__(self, other):
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


class Classes(dict): pass


class Sequence(list): pass


class Class(tuple): pass


class ClassReference(object):

    def __init__(self):
        self.name = None

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        s = "ClassReference | name=%s" % self.name
        return hash(s)


class Alternates(tuple): pass


class Ligature(tuple): pass


# ---------
# Utilities
# ---------

def readCoverage(coverage):
    if not isinstance(coverage, list):
        coverage = coverage.glyphs
    coverage = Class(coverage)
    return coverage

def nameClass(features, members):
    name = "@" + "_".join(features)
    return name

def nameLookup(features):
    return "_".join(features)
