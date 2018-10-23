#-------------------------------------------------------------------------------
# ConstantXVelocityBoundary
#-------------------------------------------------------------------------------
from PYB11Generator import *
from Boundary import *
from ConstantVelocityBoundary import *

@PYB11template("Dimension")
class ConstantXVelocityBoundary(ConstantVelocityBoundary):
    """ConstantXVelocityBoundary -- A boundary condition to enforce a constant 
x-component velocity on a given set of nodes.

This boundary is very specialized -- it explicitly works on only one 
NodeList.
"""

    typedefs = """
    typedef typename %(Dimension)s::Scalar Scalar;
    typedef typename %(Dimension)s::Vector Vector;
    typedef typename %(Dimension)s::Tensor Tensor;
    typedef typename %(Dimension)s::SymTensor SymTensor;
    typedef typename %(Dimension)s::ThirdRankTensor ThirdRankTensor;
"""

    #...........................................................................
    # Constructors
    def pyinit(self,
               nodeList = "const NodeList<%(Dimension)s>&",
               nodeIndices = "const std::vector<int>&"):
        "Construct a constant X velocity for the given nodes"

    #...........................................................................
    # Methods
    @PYB11virtual
    @PYB11const
    def enforceBoundary(self, field="Field<%(Dimension)s, Vector>&"):
        "Apply the boundary condition to the violation node values in the given Field."
        return "void"

    @PYB11virtual
    @PYB11const
    def label(self):
        "Label for restart files"
        return "std::string"
