"""
To Do:
- feature.tag vs. lookup.name
- lookup type 7
- move _load to a function and a writer
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
- is the type attribute of the Lookup object necessary?
- revisit __hash__
- zfill class and lookup names?
"""

class FeaToolsError(Exception): pass


def decompileBinaryToObject(pathOrFile):
    from fontTools.ttLib import TTFont
    from objects import Tables
    # load font
    font = TTFont(pathOrFile)
    # decompile
    tables = Tables()
    tables._load(font)
    # close
    font.close()
    # done
    return tables


def decompileBinaryToFeaSyntax(pathOrFile):
    from writers.feaSyntaxWriter import FeaSyntaxWriter
    # decompile
    tables = decompileBinaryToObject(pathOrFile)
    # write
    writer = FeaSyntaxWriter(filterRedundancies=True)
    tables["GSUB"].write(writer)
    tables["GPOS"].write(writer)
    text = writer.write()
    # done
    return text
