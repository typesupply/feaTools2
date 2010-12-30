"""
To Do:
- lookup type 7
- move _load to a function and a writer
- merge GSUB and GPOS into one table. GDEF as well, i guess.
    - rename the Table class since it won't make sense anymore.
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
"""

def decompileBinaryToObject(pathOrFile):
    from fontTools.ttLib import TTFont
    from objects import Table
    # load font
    font = TTFont(pathOrFile)
    # decompile
    tags = "GSUB".split(" ")
    tables = {}
    for tag in tags:
        table = Table()
        table.tag = tag
        if font.has_key(tag):
            table._load(font[tag].table, tag)
        tables[tag] = table
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
    text = writer.write()
    # done
    return text
