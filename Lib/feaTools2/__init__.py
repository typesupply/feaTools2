"""
To Do:
- get rid of remove glyph and rename glyph for now. the objects need to mature before conveniences are added.
- rername lookup.name to lookup.tag
- get rid of the addLanguageSystem in the writers. it only means something in .fea
  and it can be deduced through iteration.
- support GSUB lookup type 7
- support GPOS
- move type assertions from writer to attributes in the subtable objects
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
- add decompress methods that undo what compression does.
  this would be useful for taking .fea or a subset object and going back to binary.
- the ignore support in the remove glyph/should be removed process in the
  GSUB subtable object may be fragile. maybe set a special substitution Ignore value? 
- make a fontTools object writer
- make a compositor object writer
"""

class FeaToolsError(Exception): pass


def decompileBinaryToObject(pathOrFile, compress=True):
    from fontTools.ttLib import TTFont
    from feaTools2.objects import Tables
    from feaTools2.parsers.binaryParser import parseTable
    # load font
    closeFont = True
    if not isinstance(pathOrFile, TTFont):
        font = pathOrFile
        closeFont = False
    else:
        font = TTFont(pathOrFile)
    # decompile
    tables = Tables()
    if "GSUB" in font:
        table = tables["GSUB"]
        parseTable(table, font["GSUB"].table, "GSUB")
        if compress:
            table.compress()
    # close
    if closeFont:
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
