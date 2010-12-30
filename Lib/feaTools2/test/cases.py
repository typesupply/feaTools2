# -----------------------
# Compress Global Lookups
# -----------------------

compressGlobalLookups1_fea = """
languagesystem DFLT dflt;
feature TST1 {
    lookup Lookup_Test1 {
        sub A by B;
    } Lookup_Test1;
} TST1;
feature TST2 {
    lookup Lookup_Test2 {
        sub A by B;
    } Lookup_Test2;
} TST2;
""".strip()

compressGlobalLookups1_dump = """
LanguageSystem: DFLT None
Lookup: TST2_TST1_1
    LookupFlag:
        rightToLeft: False
        ignoreBaseGlyphs: False
        ignoreLigatures: False
        ignoreMarks: False
        markAttachmentType: False
    GSUBSubtable Type 1:
        backtrack: []
        lookahead: []
        target: [[[A]]]
        substitution: [[[B]]]
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup Reference: TST2_TST1_1
Feature: TST2
    Script: DFLT
        Language: None
            Include Default: True
            Lookup Reference: TST2_TST1_1
""".strip()

compressGlobalLookups2_fea = """
languagesystem DFLT dflt;
feature TST1 {
    sub A by B;
} TST1;
feature TST2 {
    sub A by B;
} TST2;
""".strip()

compressGlobalLookups2_dump = """
LanguageSystem: DFLT None
Lookup: TST2_TST1_1
    LookupFlag:
        rightToLeft: False
        ignoreBaseGlyphs: False
        ignoreLigatures: False
        ignoreMarks: False
        markAttachmentType: False
    GSUBSubtable Type 1:
        backtrack: []
        lookahead: []
        target: [[[A]]]
        substitution: [[[B]]]
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup Reference: TST2_TST1_1
Feature: TST2
    Script: DFLT
        Language: None
            Include Default: True
            Lookup Reference: TST2_TST1_1
""".strip()

compressGlobalLookups3_fea = """
languagesystem DFLT dflt;
lookup Test {
    sub A by B;
} Test;
feature TST1 {
    lookup Test;
} TST1;
feature TST2 {
    lookup Test;
} TST2;
""".strip()

compressGlobalLookups3_dump = """
LanguageSystem: DFLT None
Lookup: TST2_TST1_1
    LookupFlag:
        rightToLeft: False
        ignoreBaseGlyphs: False
        ignoreLigatures: False
        ignoreMarks: False
        markAttachmentType: False
    GSUBSubtable Type 1:
        backtrack: []
        lookahead: []
        target: [[[A]]]
        substitution: [[[B]]]
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup Reference: TST2_TST1_1
Feature: TST2
    Script: DFLT
        Language: None
            Include Default: True
            Lookup Reference: TST2_TST1_1
""".strip()

compressGlobalLookups4_fea = """
languagesystem DFLT dflt;
lookup Test1 {
    sub A by B;
} Test1;
lookup Test2 {
    sub C by D;
} Test2;
feature TST1 {
    lookup Test1;
    lookup Test2;
} TST1;
feature TST2 {
    lookup Test1;
} TST2;
""".strip()

compressGlobalLookups4_dump = """
LanguageSystem: DFLT None
Lookup: TST2_TST1_1
    LookupFlag:
        rightToLeft: False
        ignoreBaseGlyphs: False
        ignoreLigatures: False
        ignoreMarks: False
        markAttachmentType: False
    GSUBSubtable Type 1:
        backtrack: []
        lookahead: []
        target: [[[A]]]
        substitution: [[[B]]]
Feature: TST2
    Script: DFLT
        Language: None
            Include Default: True
            Lookup Reference: TST2_TST1_1
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup Reference: TST2_TST1_1
            Lookup: TST1_1
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 1:
                    backtrack: []
                    lookahead: []
                    target: [[[C]]]
                    substitution: [[[D]]]
""".strip()

# ------------------------
# Compress Feature Lookups
# ------------------------

compressFeatureLookups1_fea = """
languagesystem DFLT dflt;
lookup Lookup_Test1 {
    sub A by B;
} Lookup_Test1;
feature TST1 {
    lookup Lookup_Test1;
    sub B by C;
} TST1;
""".strip()

compressFeatureLookups1_dump = """
LanguageSystem: DFLT None
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup: TST1_1
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 1:
                    backtrack: []
                    lookahead: []
                    target: [[[A]]]
                    substitution: [[[B]]]
            Lookup: TST1_2
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 1:
                    backtrack: []
                    lookahead: []
                    target: [[[B]]]
                    substitution: [[[C]]]
""".strip()


# -----------------------------------------
# Compress Feature Default Language Lookups
# -----------------------------------------

compressFeatureDefaultLanguageLookups1_fea = """
languagesystem DFLT dflt;
languagesystem latn dflt;
languagesystem latn TRK;
languagesystem cyrl dflt;
feature TST1 {
    sub A by B;
} TST1;""".strip()

compressFeatureDefaultLanguageLookups1_dump = """
LanguageSystem: DFLT None
LanguageSystem: cyrl None
LanguageSystem: latn None
LanguageSystem: latn TRK
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup: TST1_1
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 1:
                    backtrack: []
                    lookahead: []
                    target: [[[A]]]
                    substitution: [[[B]]]
    Script: cyrl
        Language: None
            Include Default: True
    Script: latn
        Language: None
            Include Default: True
        Language: TRK
            Include Default: True
""".strip()

compressFeatureDefaultLanguageLookups2_fea = """
languagesystem DFLT dflt;
languagesystem latn dflt;
languagesystem latn TRK;
languagesystem cyrl dflt;
feature TST1 {
    sub A by B;
    script latn;
       sub C by D;
       language TRK;
           sub E by F;
    script cyrl;
       sub G by H;
} TST1;""".strip()

compressFeatureDefaultLanguageLookups2_dump = """
LanguageSystem: DFLT None
LanguageSystem: cyrl None
LanguageSystem: latn None
LanguageSystem: latn TRK
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup: TST1_1
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 1:
                    backtrack: []
                    lookahead: []
                    target: [[[A]]]
                    substitution: [[[B]]]
    Script: cyrl
        Language: None
            Include Default: True
            Lookup: TST1_2
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 1:
                    backtrack: []
                    lookahead: []
                    target: [[[G]]]
                    substitution: [[[H]]]
    Script: latn
        Language: None
            Include Default: True
            Lookup: TST1_3
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 1:
                    backtrack: []
                    lookahead: []
                    target: [[[C]]]
                    substitution: [[[D]]]
        Language: TRK
            Include Default: True
            Lookup: TST1_4
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 1:
                    backtrack: []
                    lookahead: []
                    target: [[[E]]]
                    substitution: [[[F]]]
""".strip()

compressFeatureDefaultLanguageLookups3_fea = """
languagesystem DFLT dflt;
languagesystem latn dflt;
languagesystem latn TRK;
feature TST1 {
    sub A by B;
    script latn;
       language TRK exclude_dflt;
           sub E by F;
} TST1;""".strip()

compressFeatureDefaultLanguageLookups3_dump = """
LanguageSystem: DFLT None
LanguageSystem: latn None
LanguageSystem: latn TRK
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup: TST1_1
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 1:
                    backtrack: []
                    lookahead: []
                    target: [[[A]]]
                    substitution: [[[B]]]
    Script: latn
        Language: None
            Include Default: True
        Language: TRK
            Include Default: False
            Lookup: TST1_2
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 1:
                    backtrack: []
                    lookahead: []
                    target: [[[E]]]
                    substitution: [[[F]]]
""".strip()

# -----------
# Lookup Flag
# -----------

lookupFlag1_fea = """
languagesystem DFLT dflt;
feature TST1 {
    lookupflag RightToLeft;
    sub A by B;
} TST1;
""".strip()

lookupFlag1_dump = """
LanguageSystem: DFLT None
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup: TST1_1
                LookupFlag:
                    rightToLeft: True
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 1:
                    backtrack: []
                    lookahead: []
                    target: [[[A]]]
                    substitution: [[[B]]]
""".strip()

lookupFlag2_fea = """
languagesystem DFLT dflt;
feature TST1 {
    lookupflag IgnoreMarks;
    sub A by B;
} TST1;
""".strip()

lookupFlag2_dump = """
LanguageSystem: DFLT None
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup: TST1_1
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: True
                    markAttachmentType: False
                GSUBSubtable Type 1:
                    backtrack: []
                    lookahead: []
                    target: [[[A]]]
                    substitution: [[[B]]]
""".strip()

lookupFlag3_fea = """
languagesystem DFLT dflt;
feature TST1 {
    lookupflag IgnoreBaseGlyphs;
    sub A by B;
} TST1;
""".strip()

lookupFlag3_dump = """
LanguageSystem: DFLT None
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup: TST1_1
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: True
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 1:
                    backtrack: []
                    lookahead: []
                    target: [[[A]]]
                    substitution: [[[B]]]
""".strip()

lookupFlag4_fea = """
languagesystem DFLT dflt;
feature TST1 {
    lookupflag IgnoreLigatures;
    sub A by B;
} TST1;
""".strip()

lookupFlag4_dump = """
LanguageSystem: DFLT None
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup: TST1_1
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: True
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 1:
                    backtrack: []
                    lookahead: []
                    target: [[[A]]]
                    substitution: [[[B]]]
""".strip()

lookupFlag5_fea = """
languagesystem DFLT dflt;
@test = [A];
feature TST1 {
    lookupflag MarkAttachmentType @test;
    sub A by B;
} TST1;
""".strip()

lookupFlag5_dump = """
LanguageSystem: DFLT None
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup: TST1_1
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: True
                GSUBSubtable Type 1:
                    backtrack: []
                    lookahead: []
                    target: [[[A]]]
                    substitution: [[[B]]]
""".strip()

# -----------
# GSUB Type 1
# -----------

gsubType11_fea = """
languagesystem DFLT dflt;
feature TST1 {
    sub A by B;
} TST1;
""".strip()

gsubType11_dump = """
LanguageSystem: DFLT None
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup: TST1_1
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 1:
                    backtrack: []
                    lookahead: []
                    target: [[[A]]]
                    substitution: [[[B]]]
""".strip()

gsubType12_fea = """
languagesystem DFLT dflt;
feature TST1 {
    sub [A C E] by [B D F];
} TST1;
""".strip()

gsubType12_dump = """
LanguageSystem: DFLT None
Feature: TST1
    Class: @TST1_1: [A C E]
    Class: @TST1_2: [B D F]
    Script: DFLT
        Language: None
            Include Default: True
            Lookup: TST1_1
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 1:
                    backtrack: []
                    lookahead: []
                    target: [[[@TST1_1]]]
                    substitution: [[[@TST1_2]]]
""".strip()

gsubType13_fea = """
languagesystem DFLT dflt;
feature TST1 {
    sub A by B;
    sub C by D;
    sub E by F;
} TST1;
""".strip()

gsubType13_dump = """
LanguageSystem: DFLT None
Feature: TST1
    Class: @TST1_1: [A C E]
    Class: @TST1_2: [B D F]
    Script: DFLT
        Language: None
            Include Default: True
            Lookup: TST1_1
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 1:
                    backtrack: []
                    lookahead: []
                    target: [[[@TST1_1]]]
                    substitution: [[[@TST1_2]]]
""".strip()

# -----------
# GSUB Type 3
# -----------

gsubType31_fea = """
languagesystem DFLT dflt;
feature TST1 {
    sub A from [B C];
} TST1;
""".strip()

gsubType31_dump = """
LanguageSystem: DFLT None
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup: TST1_1
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 3:
                    backtrack: []
                    lookahead: []
                    target: [[[A]]]
                    substitution: [[[B C]]]
""".strip()

# -----------
# GSUB Type 4
# -----------

gsubType41_fea = """
languagesystem DFLT dflt;
feature TST1 {
    sub A B by C;
} TST1;
""".strip()

gsubType41_dump = """
LanguageSystem: DFLT None
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup: TST1_1
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 4:
                    backtrack: []
                    lookahead: []
                    target: [[[A] [B]]]
                    substitution: [[[C]]]
""".strip()

gsubType42_fea = """
languagesystem DFLT dflt;
feature TST1 {
    sub [A B] C by D;
} TST1;
""".strip()

gsubType42_dump = """
LanguageSystem: DFLT None
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup: TST1_1
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 4:
                    backtrack: []
                    lookahead: []
                    target: [[[A] [C]] [[B] [C]]]
                    substitution: [[[D]] [[D]]]
""".strip()

# -----------
# GSUB Type 6
# -----------

gsubType61_fea = """
languagesystem DFLT dflt;
feature TST1 {
    sub A B C' E F by D;
} TST1;
""".strip()

gsubType61_dump = """
LanguageSystem: DFLT None
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup: TST1_1
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 6:
                    backtrack: [[A] [B]]
                    lookahead: [[E] [F]]
                    target: [[[C]]]
                    substitution: [[[D]]]
""".strip()

gsubType62_fea = """
languagesystem DFLT dflt;
feature TST1 {
    sub A B' C by D;
    sub A E' C by F;
} TST1;
""".strip()

gsubType62_dump = """
LanguageSystem: DFLT None
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup: TST1_1
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 6:
                    backtrack: [[A]]
                    lookahead: [[C]]
                    target: [[[B]]]
                    substitution: [[[D]]]
                GSUBSubtable Type 6:
                    backtrack: [[A]]
                    lookahead: [[C]]
                    target: [[[E]]]
                    substitution: [[[F]]]
""".strip()

gsubType63_fea = """
languagesystem DFLT dflt;
feature TST1 {
    ignore sub E F' G;
    sub A B' C by D;
} TST1;
""".strip()

gsubType63_dump = """
LanguageSystem: DFLT None
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup: TST1_1
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 6:
                    backtrack: [[E]]
                    lookahead: [[G]]
                    target: [[[F]]]
                    substitution: []
                GSUBSubtable Type 6:
                    backtrack: [[A]]
                    lookahead: [[C]]
                    target: [[[B]]]
                    substitution: [[[D]]]
""".strip()

gsubType64_fea = """
languagesystem DFLT dflt;
feature TST1 {
    sub A B C' D' F G by E;
} TST1;
""".strip()

gsubType64_dump = """
LanguageSystem: DFLT None
Feature: TST1
    Script: DFLT
        Language: None
            Include Default: True
            Lookup: TST1_1
                LookupFlag:
                    rightToLeft: False
                    ignoreBaseGlyphs: False
                    ignoreLigatures: False
                    ignoreMarks: False
                    markAttachmentType: False
                GSUBSubtable Type 6:
                    backtrack: [[A] [B]]
                    lookahead: [[F] [G]]
                    target: [[[C] [D]]]
                    substitution: [[[E]]]
""".strip()
