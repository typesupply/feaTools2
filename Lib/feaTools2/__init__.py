"""
To Do:
- feature.tag vs. lookup.name
- lookup type 7
- move type assertions from writer to attributes in the subtable objects
- add decompress methods that undo what compression does.
  this would be useful for taking .fea or a subset object and going back to binary.
- make a fontTools object writer
- make a compositor object writer
- add some scripting functions
    remove glyph(s)
    rename glyph(s)
    cleanup (removes unnecessary stuff)
- make objects descend from defcon's base object
- handle markAttachmentType properly
- revisit __hash__
- zfill class and lookup names?
- should there be any checking for overwrites or bad data? should the objects be responsisble for this?
    - duplicate feature tag
    - existing class
    - duplicate script tag
    - duplicate language tag
    - duplicate lookup name
    - lookup reference to unknown lookup
    - class reference to unknown class
    - target/substitution/backtrack/lookup structure
    - GSUB and GPOS subtables in the same lookup
- get rid of the addLanguageSystem writer. it only means something in .fea
  and it can be deduced through iteration.
"""

class FeaToolsError(Exception): pass


def decompileBinaryToObject(pathOrFile, compress=True):
    from fontTools.ttLib import TTFont
    from feaTools2.objects import Tables
    from feaTools2.parsers.binaryParser import parseTable
    # load font
    font = TTFont(pathOrFile)
    # decompile
    tables = Tables()
    if "GSUB" in font:
        table = tables["GSUB"]
        parseTable(table, font["GSUB"].table, "GSUB")
        if compress:
            table.compress()
    # close
    font.close()
    # done
    return tables


def decompileBinaryToFeaSyntax(pathOrFile):
    from feaTools2.writers.feaSyntaxWriter import FeaSyntaxWriter
    # decompile
    tables = decompileBinaryToObject(pathOrFile)
    # write
    writer = FeaSyntaxWriter(filterRedundancies=True)
    tables["GSUB"].write(writer)
    tables["GPOS"].write(writer)
    text = writer.write()
    # done
    return text
