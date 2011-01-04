import tempfile
import os
from fontTools.ttLib import TTLibError
from fontTools.agl import AGL2UV
from defcon import Font
from ufo2fdk import OTFCompiler
from feaTools2 import decompileBinaryToObject
from feaTools2.writers.dumpWriter import DumpWriter
from feaTools2.test.cases import *

def compileDecompileCompareDumps(features, expectedDump):
    # make the font
    font = Font()
    font.info.unitsPerEm = 1000
    font.info.ascender = 750
    font.info.descender = -250
    font.info.xHeight = 500
    font.info.capHeight = 750
    font.info.familyName = "Test"
    font.info.styleName = "Regular"
    glyphNames = [i for i in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
    for glyphName in glyphNames:
        font.newGlyph(glyphName)
        glyph = font[glyphName]
        glyph.unicode = AGL2UV.get(glyphName)
    font.features.text = features
    # compile to OTF
    handle, path = tempfile.mkstemp()
    compiler = OTFCompiler()
    errors = compiler.compile(font, path)["makeotf"]
    # extract the features
    try:
        tables = decompileBinaryToObject(path)
    # print compiler errors
    except TTLibError:
        print errors
    # get rid of the temp file
    finally:
        os.remove(path)
    # dump
    writer = DumpWriter()
    tables["GSUB"].write(writer)
    dump = writer.dump()
    # compare
    compareDumps(expectedDump, dump)

def compareDumps(dump1, dump2):
    if dump1 == dump2:
        return
    print
    print "Expected:"
    print "---------"
    print dump1
    print
    print "Got:"
    print "----"
    print dump2
    print
    dump1 = dump1.splitlines()
    dump2 = dump2.splitlines()
    index = 0
    for index, line1 in enumerate(dump1):
        if index > len(dump2):
            break
        if line1 != dump2[index]:
            break
    print "First difference at line: %d" % (index + 1)
    print

# ------------------
# Lookup Compression
# ------------------

def testGlobalLookupCompression():
    """
    >>> compileDecompileCompareDumps(compressGlobalLookups1_fea, compressGlobalLookups1_dump)
    >>> compileDecompileCompareDumps(compressGlobalLookups2_fea, compressGlobalLookups2_dump)
    >>> compileDecompileCompareDumps(compressGlobalLookups3_fea, compressGlobalLookups3_dump)
    >>> compileDecompileCompareDumps(compressGlobalLookups4_fea, compressGlobalLookups4_dump)
    """

def testFeatureLookupCompression():
    """
    >>> compileDecompileCompareDumps(compressFeatureLookups1_fea, compressFeatureLookups1_dump)
    """

def testFeatureDefaultLanguageLookupCompression():
    """
    >>> compileDecompileCompareDumps(compressFeatureDefaultLanguageLookups1_fea, compressFeatureDefaultLanguageLookups1_dump)
    >>> compileDecompileCompareDumps(compressFeatureDefaultLanguageLookups2_fea, compressFeatureDefaultLanguageLookups2_dump)
    >>> compileDecompileCompareDumps(compressFeatureDefaultLanguageLookups3_fea, compressFeatureDefaultLanguageLookups3_dump)
    """

# -----------
# Lookup Flag
# -----------

def testLookupFlag():
    """
    >>> compileDecompileCompareDumps(lookupFlag1_fea, lookupFlag1_dump)
    >>> compileDecompileCompareDumps(lookupFlag2_fea, lookupFlag2_dump)
    >>> compileDecompileCompareDumps(lookupFlag3_fea, lookupFlag3_dump)
    >>> compileDecompileCompareDumps(lookupFlag4_fea, lookupFlag4_dump)
    >>> compileDecompileCompareDumps(lookupFlag5_fea, lookupFlag5_dump)
    """

# -----------
# GSUB Type 1
# -----------

def testGSUBType1():
    """
    >>> compileDecompileCompareDumps(gsubType11_fea, gsubType11_dump)
    >>> compileDecompileCompareDumps(gsubType12_fea, gsubType12_dump)
    >>> compileDecompileCompareDumps(gsubType13_fea, gsubType13_dump)
    """

# -----------
# GSUB Type 3
# -----------

def testGSUBType3():
    """
    >>> compileDecompileCompareDumps(gsubType31_fea, gsubType31_dump)
    """

# -----------
# GSUB Type 4
# -----------

def testGSUBType4():
    """
    >>> compileDecompileCompareDumps(gsubType41_fea, gsubType41_dump)
    >>> compileDecompileCompareDumps(gsubType42_fea, gsubType42_dump)
    """

# -----------
# GSUB Type 6
# -----------

def testGSUBType6():
    """
    >>> compileDecompileCompareDumps(gsubType61_fea, gsubType61_dump)
    >>> compileDecompileCompareDumps(gsubType62_fea, gsubType62_dump)
    >>> compileDecompileCompareDumps(gsubType63_fea, gsubType63_dump)
    >>> compileDecompileCompareDumps(gsubType64_fea, gsubType64_dump)
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
