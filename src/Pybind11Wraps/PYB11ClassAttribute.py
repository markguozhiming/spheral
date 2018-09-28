from PYB11utils import *
import sys, inspect

#-------------------------------------------------------------------------------
# PYB11generateClassAttributes
#
# Bind the class attributes
#-------------------------------------------------------------------------------
def PYB11GenerateClassAttributes(klass, klassinst, klassattrs, ss):

    # Find any base attributes so we can screen them out
    battrs = []
    for bklass in inspect.getmro(klass)[1:]:
        bklassinst = bklass()
        battrs += [x for x in dir(bklassinst) if isinstance(eval("bklassinst.%s" % x), PYB11ClassAttribute)]

    PYB11attrs = [x for x in dir(klass) if isinstance(eval("klass.%s" % x), PYB11ClassAttribute)]
    if PYB11attrs:
        ss("\n    // Properties\n")

    for attrname in PYB11attrs:
        exec('klassinst.%s("%s", klassattrs, ss)' % (attrname, attrname))
    ss("\n")

    return

#-------------------------------------------------------------------------------
# The base class for attributes, most of the implementation
#-------------------------------------------------------------------------------
class PYB11ClassAttribute:

    def __init__(self,
                 static,
                 pyname,
                 cppname,
                 doc,
                 deftype):
        self.static = static
        self.pyname = pyname
        self.cppname = cppname
        self.doc = doc
        self.deftype = deftype
        return

    def __call__(self,
                 name,
                 klassattrs,
                 ss):
        if self.pyname:
            pyname = self.pyname
        else:
            pyname = name
        if self.cppname:
            cppname = self.cppname
        else:
            cppname = name
        if self.static:
            ss('    obj.def_%s_static("%s", ' % (self.deftype, pyname))
        else:
            ss('    obj.def_%s("%s", ' % (self.deftype, pyname))
        ss(("&%(namespace)s%(cppname)s::" % klassattrs) + cppname)
        if self.doc:
            ss(',\n            "%s"' % self.doc)
        ss(");\n")
        return

#-------------------------------------------------------------------------------
# readwrite
#-------------------------------------------------------------------------------
class PYB11readwrite(PYB11ClassAttribute):

    def __init__(self,
                 static = False,
                 pyname = None,
                 cppname = None,
                 doc = None):
        PYB11ClassAttribute.__init__(self, static, pyname, cppname, doc, "readwrite")

#-------------------------------------------------------------------------------
# readonly
#-------------------------------------------------------------------------------
class PYB11readonly(PYB11ClassAttribute):

    def __init__(self,
                 static = False,
                 pyname = None,
                 cppname = None,
                 doc = None):
        PYB11ClassAttribute.__init__(self, static, pyname, cppname, doc, "readonly")

