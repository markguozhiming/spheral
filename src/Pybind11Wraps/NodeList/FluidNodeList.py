from PYB11Generator import *
from NodeList import NodeList
from RestartMethods import *

#-------------------------------------------------------------------------------
# FluidNodeList template
#-------------------------------------------------------------------------------
@PYB11template("Dimension")
@PYB11module("SpheralNodeList")
@PYB11dynamic_attr
class FluidNodeList(NodeList):
    "Spheral FluidNodeList base class in %(Dimension)s, i.e.,  the NodeList for fluid hydrodynamics."

    typedefs = """
    typedef typename %(Dimension)s::Scalar Scalar;
    typedef typename %(Dimension)s::Vector Vector;
    typedef typename %(Dimension)s::Tensor Tensor;
    typedef typename %(Dimension)s::SymTensor SymTensor;
    typedef Field<%(Dimension)s, Scalar> ScalarField;
    typedef Field<%(Dimension)s, Vector> VectorField;
    typedef Field<%(Dimension)s, Tensor> TensorField;
    typedef Field<%(Dimension)s, SymTensor> SymTensorField;
"""

    def pyinit(self,
               name = "std::string",
               eos = "EquationOfState<%(Dimension)s>&",
               numInternal = ("int", "0"),
               numGhost = ("int", "0"),
               hmin = ("double", "1e-20"),
               hmax = ("double", "1e20"),
               hminratio = ("double", "0.1"),
               nPerh = ("double", "2.01"),
               maxNumNeighbors = ("int", "500"),
               rhoMin = ("double", "1e-10"),
               rhoMax = ("double", "1e100")):
        "Constructor for a FluidNodeList class."
        return

    @PYB11const
    def massDensity(self):
        "The mass density field"
        return "const ScalarField&"

    @PYB11const
    def specificThermalEnergy(self):
        "The specific thermal energy field"
        return "const ScalarField&"

    @PYB11virtual
    @PYB11const
    def pressure(self, result="ScalarField&"):
        "Compute the current pressure, storing the result in the argument ScalarField."
        return "void"

    @PYB11virtual
    @PYB11const
    def temperature(self, result="ScalarField&"):
        "Compute the current temperature, storing the result in the argument ScalarField."
        return "void"

    @PYB11virtual
    @PYB11const
    def soundSpeed(self, result="ScalarField&"):
        "Compute the current sound speed, storing the result in the argument ScalarField."
        return "void"

    @PYB11virtual
    @PYB11const
    def volume(self, result="ScalarField&"):
        "Compute the current volume, storing the result in the argument ScalarField."
        return "void"

    @PYB11virtual
    @PYB11const
    def linearMomentum(self, result="VectorField&"):
        "Compute the current linear momentum, storing the result in the argument ScalarField."
        return "void"

    @PYB11virtual
    @PYB11const
    def totalEnergy(self, result="ScalarField&"):
        "Compute the current total energy, storing the result in the argument ScalarField."
        return "void"

    @PYB11const
    def equationOfState(self):
        "Return the equation of state object this FluidNodeList is associated with."
        return "const EquationOfState<%(Dimension)s>&"

    @PYB11cppname("equationOfState")
    def setequationOfState(self, equationOfState="const EquationOfState<%(Dimension)s>&"):
        "Set the equation of state for this FluidNodeList."
        return "void"

    # Comparison
    def __eq__(self):
        "Equivalence test with another FluidNodeList"

    def __ne__(self):
        "Inequivalence test with another FluidNodeList"

    # Methods used for properties
    @PYB11ignore
    @PYB11cppname("rhoMin")
    @PYB11const
    def getrhoMin(self):
        return "double"

    @PYB11ignore
    @PYB11cppname("rhoMin")
    def setrhoMin(self, val="const double"):
        return "void"

    @PYB11ignore
    @PYB11cppname("rhoMax")
    @PYB11const
    def getrhoMax(self):
        return "double"

    @PYB11ignore
    @PYB11cppname("rhoMax")
    def setrhoMax(self, val="const double"):
        return "void"

    # Properties
    rhoMin = property(getrhoMin, setrhoMin, doc="The minimum allowed mass density.")
    rhoMax = property(getrhoMax, setrhoMax, doc="The maximum allowed mass density.")

#-------------------------------------------------------------------------------
# Inject the restart methods
#-------------------------------------------------------------------------------
PYB11inject(RestartMethods, FluidNodeList)
