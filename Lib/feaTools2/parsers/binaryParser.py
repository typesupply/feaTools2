def parseTable(writer, table, tableTag, excludeFeatures=None):
    if excludeFeatures is None:
        excludeFeatures = []
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
            if featureTag in excludeFeatures:
                continue
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
                if featureTag in excludeFeatures:
                    continue
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
        feature = writer.addFeature(featureTag)
        parseFeature(feature, table, tableTag, records)

def parseFeature(writer, table, tableTag, records):
    for (scriptTag, languageTag, lookupRecords) in records:
        writer.addScript(scriptTag)
        parseScript(writer, table, tableTag, languageTag, lookupRecords)

def parseScript(writer, table, tableTag, languageTag, lookupRecords):
    language = writer.addLanguage(languageTag)
    parseLanguage(writer, table, tableTag, lookupRecords)

def parseLanguage(writer, table, tableTag, lookupRecords):
    for lookupRecord in lookupRecords:
        lookup = writer.addLookup(None)
        parseLookup(lookup, table, tableTag, lookupRecord)

def parseLookup(writer, table, tableTag, lookupRecord):
    parseLookupFlag(writer, lookupRecord.LookupFlag)
    for subtableRecord in lookupRecord.SubTable:
        parseSubtable(writer, table, tableTag, lookupRecord.LookupType, subtableRecord)

def parseLookupFlag(writer, lookupFlag):
    kwargs = dict(
        rightToLeft=bool(lookupFlag & 0x0001),
        ignoreBaseGlyphs=bool(lookupFlag & 0x0002),
        ignoreLigatures=bool(lookupFlag & 0x0004),
        ignoreMarks=bool(lookupFlag & 0x0008),
        markAttachmentType=bool(lookupFlag & 0xFF00)
    )
    writer.addLookupFlag(**kwargs)

def parseSubtable(writer, table, tableTag, type, subtableRecord):
    if tableTag == "GSUB":
        if type == 1:
            parseGSUBLookupType1(writer, subtableRecord)
        elif type == 2:
            parseGSUBLookupType2(writer, subtableRecord)
        elif type == 3:
            parseGSUBLookupType3(writer, subtableRecord)
        elif type == 4:
            parseGSUBLookupType4(writer, subtableRecord)
        elif type == 5:
            parseGSUBLookupType5(writer, subtableRecord)
        elif type == 6:
            parseGSUBLookupType6(writer, table, tableTag, subtableRecord)
        elif type == 7:
            parseGSUBLookupType7(writer, subtableRecord)
        else:
            raise FeaToolsError, "Unknown GSUB subtable type %d" % type
    else:
        raise NotImplementedError

def parseGSUBLookupType1(writer, subtable):
    targetClass = []
    substitutionClass = []
    for t, s in sorted(subtable.mapping.items()):
        targetClass.append(t)
        substitutionClass.append(s)
    targetSequence = [targetClass]
    substitutionSequence = [substitutionClass]
    target = [targetSequence]
    substitution = [substitutionSequence]
    writer.addGSUBSubtable(target=target, substitution=substitution, type=1)

def parseGSUBLookupType3(writer, subtable):
    target = []
    substitution = []
    for t, s in sorted(subtable.alternates.items()):
        # wrap it in a class
        t = [t]
        # wrap the class in a sequence
        t = [t]
        # store
        target.append(t)
        # wrap it in a class
        s = list(s)
        # wrap the class in a sequence
        s = [s]
        # store
        substitution.append(s)
    writer.addGSUBSubtable(target=target, substitution=substitution, type=3)

def parseGSUBLookupType4(writer, subtable):
    target = []
    substitution = []
    for firstGlyph, parts in sorted(subtable.ligatures.items()):
        for part in parts:
            # get the parts
            t = [firstGlyph] + part.Component
            # wrap the parts in classes
            t = [[i] for i in t]
            # store
            target.append(t)
            # get the substitution
            s = part.LigGlyph
            # wrap it in a class
            s = [s]
            # wrap the class in a sequence
            s = [s]
            # store
            substitution.append(s)
    writer.addGSUBSubtable(target=target, substitution=substitution, type=4)

def parseGSUBLookupType6(writer, table, tableTag, subtable):
    from feaTools2.objects import Table
    assert subtable.Format == 3, "Stop being lazy."
    backtrack = [readCoverage(i) for i in reversed(subtable.BacktrackCoverage)]
    lookahead = [readCoverage(i) for i in subtable.LookAheadCoverage]
    input = [readCoverage(i) for i in subtable.InputCoverage]
    # the "ignore" rule generates subtables with an empty SubstLookup
    if not subtable.SubstLookupRecord:
        target = [list(input)]
        substitution = []
    # a regular contextual rule
    else:
        target = []
        substitution = []
        assert len(subtable.SubstLookupRecord) == 1, "Does this ever happen?"
        for substLookup in subtable.SubstLookupRecord:
            index = substLookup.LookupListIndex
            lookupRecord = table.LookupList.Lookup[index]
            # make a dummy table
            dummyTable = Table()
            dummyTable.tag = tableTag
            # add a dummpy lookup
            dummyLookup = dummyTable.addLookup("DummyLookup")
            # write the data into the objects
            parseLookup(dummyLookup, table, tableTag, lookupRecord)
            # extract the lookup
            lookup = dummyLookup
            # XXX potential problem here:
            # theoretically this nested lookup could have a flag that is
            # different than the flag of the lookup that contains this
            # subtable. i can't think of a way to do this with the
            # .fea syntax, so i'm not worrying about it right now.
            assert len(lookup.subtables) == 1, "Does this ever happen?"
            loadedSubtable = lookup.subtables[0]
            for sequenceIndex, targetSequence in enumerate(loadedSubtable.target):
                substitutionSequence = lookup.subtables[0].substitution[sequenceIndex]
                if loadedSubtable.type == 1:
                    assert len(input) == 1, "Does this ever happen?"
                    newTargetSequence = []
                    newSubstitutionSequence = []
                    for classIndex, targetClass in enumerate(targetSequence):
                        newTargetClass = []
                        newSubstitutionClass = []
                        for memberIndex, t in enumerate(targetClass):
                            if t in input[0]:
                                newTargetClass.append(t)
                                s = substitutionSequence[classIndex][memberIndex]
                                newSubstitutionClass.append(s)
                        if newTargetClass:
                            newTargetSequence.append(newTargetClass)
                            newSubstitutionSequence.append(newSubstitutionClass)
                elif loadedSubtable.type == 4:
                    if targetSequence != input:
                        print
                        print "GSUB question"
                        print targetSequence
                        print input
                        print
                    else:
                        newTargetSequence = targetSequence
                        newSubstitutionSequence = substitutionSequence
                else:
                    raise NotImplementedError
                target.append(newTargetSequence)
                substitution.append(newSubstitutionSequence)
    writer.addGSUBSubtable(target=target, substitution=substitution, type=6, backtrack=backtrack, lookahead=lookahead)

def readCoverage(coverage):
    if not isinstance(coverage, list):
        coverage = coverage.glyphs
    coverage = list(coverage)
    return coverage