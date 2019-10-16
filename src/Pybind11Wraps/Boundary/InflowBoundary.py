#-------------------------------------------------------------------------------
# InflowBoundary
#-------------------------------------------------------------------------------
from PYB11Generator import *
from Boundary import *
from Physics import *
from BoundaryAbstractMethods import *
from PhysicsAbstractMethods import *
from RestartMethods import *

@PYB11template("Dimension")
class InflowBoundary(Boundary, Physics):
    """InflowBoundary -- creates inflow ghost images, which become internal nodes
as they cross the specified boundary plane."""

    PYB11typedefs = """
    typedef typename %(Dimension)s::Scalar Scalar;
    typedef typename %(Dimension)s::Vector Vector;
    typedef typename %(Dimension)s::Tensor Tensor;
    typedef typename %(Dimension)s::SymTensor SymTensor;
    typedef typename %(Dimension)s::ThirdRankTensor ThirdRankTensor;
    typedef typename %(Dimension)s::FacetedVolume FacetedVolume;
    typedef typename Physics<%(Dimension)s>::TimeStepType TimeStepType;
    typedef GeomPlane<%(Dimension)s> Plane;
"""

    #...........................................................................
    # Constructors
    def pyinit(self,
               nodeList = "NodeList<%(Dimension)s>&",
               plane = "const GeomPlane<%(Dimension)s>&"):
        "Constructor"

    #...........................................................................
    # Methods
    @PYB11virtual
    def initializeProblemStartup(self):
        "After physics have been initialized we take a snapshot of the node state."
        return "void"

    @PYB11virtual
    def finalize(self,
                 time = "const Scalar",
                 dt = "const Scalar",
                 dataBase = "DataBase<%(Dimension)s>&",
                 state = "State<%(Dimension)s>&",
                 derivs = "StateDerivatives<%(Dimension)s>&"):
        """Packages might want a hook to do some post-step finalizations.
Really we should rename this post-step finalize."""
        return "void"

    #...........................................................................
    @PYB11template("DataType")
    @PYB11returnpolicy("reference")
    def storedValues(self,
                     fieldName = "const std::string",
                     dummy = ("const %(DataType)s&", "%(DataType)s()")):
        "Get the stored data for generating ghost nodes."
        return "std::vector<%(DataType)s>&"

    storedValues_int =             PYB11TemplateMethod(storedValues, "int")
    storedValues_Scalar =          PYB11TemplateMethod(storedValues, "Scalar")
    storedValues_Vector =          PYB11TemplateMethod(storedValues, "Vector")
    storedValues_Tensor =          PYB11TemplateMethod(storedValues, "Tensor")
    storedValues_SymTensor =       PYB11TemplateMethod(storedValues, "SymTensor")
    storedValues_ThirdRankTensor = PYB11TemplateMethod(storedValues, "ThirdRankTensor")
    storedValues_FacetedVolume =   PYB11TemplateMethod(storedValues, "FacetedVolume")
    storedValues_vectorScalar =    PYB11TemplateMethod(storedValues, "std::vector<Scalar>")
    storedValues_vectorVector =    PYB11TemplateMethod(storedValues, "std::vector<Vector>")

    #...........................................................................
    @PYB11template("DataType")
    @PYB11returnpolicy("reference")
    @PYB11cppname("storedValues")
    def storedValuesF(self,
                      field = "const Field<%(Dimension)s, %(DataType)s>&"):
        "Get the stored data for generating ghost nodes."
        return "std::vector<%(DataType)s>&"

    storedValuesF_int =             PYB11TemplateMethod(storedValuesF, "int", pyname="storedValues")
    storedValuesF_Scalar =          PYB11TemplateMethod(storedValuesF, "Scalar", pyname="storedValues")
    storedValuesF_Vector =          PYB11TemplateMethod(storedValuesF, "Vector", pyname="storedValues")
    storedValuesF_Tensor =          PYB11TemplateMethod(storedValuesF, "Tensor", pyname="storedValues")
    storedValuesF_SymTensor =       PYB11TemplateMethod(storedValuesF, "SymTensor", pyname="storedValues")
    storedValuesF_ThirdRankTensor = PYB11TemplateMethod(storedValuesF, "ThirdRankTensor", pyname="storedValues")
    storedValuesF_FacetedVolume =   PYB11TemplateMethod(storedValuesF, "FacetedVolume", pyname="storedValues")
    storedValuesF_vectorScalar =    PYB11TemplateMethod(storedValuesF, "std::vector<Scalar>", pyname="storedValues")
    storedValuesF_vectorVector =    PYB11TemplateMethod(storedValuesF, "std::vector<Vector>", pyname="storedValues")

    #...........................................................................
    # Properties
    numInflowNodes = PYB11property(doc="Number of nodes in inflow stencil")
    nodeList = PYB11property(doc="The NodeList we're allowing to flow into the problem")
    plane = PYB11property(doc="The inflow plane")

#-------------------------------------------------------------------------------
# Inject methods
#-------------------------------------------------------------------------------
PYB11inject(RestartMethods, InflowBoundary)
PYB11inject(BoundaryAbstractMethods, InflowBoundary, virtual=True, pure_virtual=False)
PYB11inject(PhysicsAbstractMethods, InflowBoundary, virtual=True, pure_virtual=False)
