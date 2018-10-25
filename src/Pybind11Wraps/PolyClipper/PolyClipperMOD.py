"""
PolyClipper module.

Binds the PolyClipper geometry operations for clipping polygons & polyhedra.
"""

from PYB11Generator import *
from CXXTypesMOD import *
import types

# Include files.
includes = ['"Geometry/polyclipper.hh"']

namespaces = ["PolyClipper"]

#-------------------------------------------------------------------------------
# Helper to add methods to Planes.
#-------------------------------------------------------------------------------
@PYB11ignore
def addPlaneMethods(cls, ndim):

    # Constructors
    def pyinit0(self):
        "Default constructor"

    def pyinit1(self,
                rhs = "const Plane%id" % ndim):
        "Copy constructor"

    def pyinit2(self,
                dist = "double",
                normal = "const Plane%id::Vector&" % ndim):
        "Construct with a distance and normal."

    def pyinit3(self,
                point = "const Plane%id::Vector&" % ndim,
                normal = "const Plane%id::Vector&" % ndim):
        "Construct with a point and normal."

    # Attributes
    dist = PYB11readwrite(doc="The distance to the origin along the normal.")
    normal = PYB11readwrite(doc="The normal to the plane.")

    for __x in [x for x in dir() if type(eval(x)) == types.FunctionType]: 
        exec("cls.%s = %s" % (__x, __x))

#-------------------------------------------------------------------------------
# Helper to add methods for Vertex.
#-------------------------------------------------------------------------------
@PYB11ignore
def addVertexMethods(cls, ndim):

    # Constructors
    def pyinit0(self):
        "Default constructor"

    def pyinit1(rhs = "const Vertex%id" % ndim):
        "Copy constructor"

    def pyinit2(position = "const Plane%id::Vector&" % ndim):
        "Construct with a position."

    def pyinit3(position = "const Plane%id::Vector&" % ndim,
                c = "int"):
        "Construct with a position and initial compare flag."

    # Attributes
    position = PYB11readwrite(doc="The position of the vertex.")
    neighbors = PYB11readwrite(doc="The connectivty of the vertex.")
    comp = PYB11readwrite(doc="The current comparison flag.")
    ID = PYB11readwrite(doc="The ID or index of the vertex.")

    def __eq__(self, other="py::self"):
        return

    for x in [x for x in dir() if type(eval(x)) == types.FunctionType]: 
        exec("cls.%s = %s" % (x, x))

#-------------------------------------------------------------------------------
# Plane2d
#-------------------------------------------------------------------------------
@PYB11cppname("Plane2d")
class PolyClipperPlane2d:
    """Plane class for polyclipper in 2 dimensions."""

addPlaneMethods(PolyClipperPlane2d, 2)

#-------------------------------------------------------------------------------
# Plane3d
#-------------------------------------------------------------------------------
@PYB11cppname("Plane3d")
class PolyClipperPlane3d:
    """Plane class for polyclipper in 3 dimensions."""

addPlaneMethods(PolyClipperPlane3d, 3)

#-------------------------------------------------------------------------------
# Vertex2d
#-------------------------------------------------------------------------------
@PYB11cppname("Vertex2d")
class Vertex2d:
    """Vertex class for polyclipper in 2 dimensions."""

addVertexMethods(Vertex2d, 2)

#-------------------------------------------------------------------------------
# Vertex3d
#-------------------------------------------------------------------------------
@PYB11cppname("Vertex3d")
class Vertex3d:
    """Vertex class for polyclipper in 3 dimensions."""

addVertexMethods(Vertex3d, 3)

#-------------------------------------------------------------------------------
# Polygon
#-------------------------------------------------------------------------------
PYB11namespace("PolyClipper")
class Polygon:

    def pyinit(self):
        "Default constructor"

    def pyinit1(self, rhs="const Polygon&"):
        "Copy constructor"

    @PYB11cppname("size")
    @PYB11const
    def __len__(self):
        return "unsigned"

    @PYB11cppname("operator[]")
    @PYB11returnpolicy("reference_internal")
    def __getitem__(self, i="size_t"):
        return "Vertex2d&"

    @PYB11implementation("[](Polygon& self, size_t i, const Vertex2d& v) { if (i >= self.size()) throw py::index_error(); self[i] = v; }") 
    def __setitem__(self, i="size_t", v="Vertex2d&"):
        "Set a value"

    @PYB11implementation("[](const Polygon& self) { return py::make_iterator(self.begin(), self.end()); }")
    def __iter__(self):
        "Python iteration through a Polygon."

#-------------------------------------------------------------------------------
# Polyhedron
#-------------------------------------------------------------------------------
PYB11namespace("PolyClipper")
class Polyhedron:

    def pyinit(self):
        "Default constructor"

    def pyinit1(self, rhs="const Polyhedron&"):
        "Copy constructor"

    @PYB11cppname("size")
    @PYB11const
    def __len__(self):
        return "unsigned"

    @PYB11cppname("operator[]")
    @PYB11returnpolicy("reference_internal")
    def __getitem__(self, i="size_t"):
        return "Vertex3d&"

    @PYB11implementation("[](Polyhedron& self, size_t i, const Vertex3d& v) { if (i >= self.size()) throw py::index_error(); self[i] = v; }") 
    def __setitem__(self, i="size_t", v="Vertex3d&"):
        "Set a value"

    @PYB11implementation("[](const Polyhedron& self) { return py::make_iterator(self.begin(), self.end()); }")
    def __iter__(self):
        "Python iteration through a Polyhedron."

#-------------------------------------------------------------------------------
# Polygon methods.
#-------------------------------------------------------------------------------
@PYB11namespace("PolyClipper")
def initializePolygon(poly, positions, neighbors):
    "Initialize a PolyClipper::Polygon from vertex positions and vertex neighbors."

@PYB11namespace("PolyClipper")
def polygon2string(poly, positions, neighbors):
    "Return a formatted string representation for a PolyClipper::Polygon."

@PYB11namespace("PolyClipper")
def convertToPolygon(polygon, Spheral_polygon):
    "Construct a PolyClipper::Polygon from a Spheral::Polygon."

@PYB11namespace("PolyClipper")
def convertFromPolygon(Spheral_polygon, polygon):
    "Construct a Spheral::Polygon from a PolyClipper::Polygon."

@PYB11namespace("PolyClipper")
def moments(zerothMoment = "double&",
            firstMoment = "Spheral::Dim<2>::Vector&",
            poly = "const Polygon&"):
    "Compute the zeroth and first moment of a PolyClipper::Polygon."
    return "void"

@PYB11namespace("PolyClipper")
def clipPolygon(poly, planes):
    "Clip a PolyClipper::Polygon with a collection of planes."

@PYB11namespace("PolyClipper")
def collapseDegenerates(poly = "Polygon&",
                        tol = "const double"):
    "Collapse edges in a PolyClipper::Polygon below the given tolerance."
    return "void"

@PYB11namespace("PolyClipper")
def splitIntoTriangles(poly = "const Polygon&",
                       tol = ("const double", "0.0")):
    "Split a PolyClipper::Polygon into triangles.\n"
    "The result is returned as a vector<vector<int>>, where each inner vector is a triple of\n"
    "ints representing vertex indices in the input Polygon."
    return "std::vector<std::vector<int>>"

#-------------------------------------------------------------------------------
# Polyhedron methods.
#-------------------------------------------------------------------------------
@PYB11namespace("PolyClipper")
def initializePolyhedron(poly, positions, neighbors):
    "Initialize a PolyClipper::Polyhedron from vertex positions and vertex neighbors."

@PYB11namespace("PolyClipper")
def polyhedron2string(poly, positions, neighbors):
    "Return a formatted string representation for a PolyClipper::Polyhedron."

@PYB11namespace("PolyClipper")
def convertToPolyhedron(polyhedron, Spheral_polyhedron):
    "Construct a PolyClipper::Polyhedron from a Spheral::Polyhedron."

@PYB11namespace("PolyClipper")
def convertFromPolyhedron(Spheral_polyhedron, polyhedron):
    "Construct a Spheral::Polyhedron from a PolyClipper::Polyhedron."

@PYB11namespace("PolyClipper")
def moments(zerothMoment = "double&",
            firstMoment = "Spheral::Dim<3>::Vector&",
            poly = "const Polyhedron&"):
    "Compute the zeroth and first moment of a PolyClipper::Polyhedron."
    return "void"

@PYB11namespace("PolyClipper")
def clipPolyhedron(poly, planes):
    "Clip a PolyClipper::Polyhedron with a collection of planes."

@PYB11namespace("PolyClipper")
def collapseDegenerates(poly = "Polyhedron&",
                        tol = "const double"):
    "Collapse edges in a PolyClipper::Polyhedron below the given tolerance."
    return "void"

@PYB11namespace("PolyClipper")
def splitIntoTetrahedra(poly = "const Polyhedron&",
                        tol = ("const double", "0.0")):
    "Split a PolyClipper::Polyhedron into tetrahedra.\n"
    "The result is returned as a vector<vector<int>>, where each inner vector is a set of four\n"
    "ints representing vertex indices in the input Polyhedron."
    return "std::vector<std::vector<int>>"
