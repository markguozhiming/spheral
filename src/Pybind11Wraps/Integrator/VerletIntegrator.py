#-------------------------------------------------------------------------------
# VerletIntegrator
#-------------------------------------------------------------------------------
from PYB11Generator import *
from IntegratorAbstractMethods import *
from Integrator import *

@PYB11template("Dimension")
@PYB11cppname("Verlet")
class VerletIntegrator(Integrator):
    """Second-order in time explicit Verlet time integration scheme
This method is symplectic in the absence of dissipation."""

    typedefs = """
    typedef typename %(Dimension)s::Scalar Scalar;
    typedef typename %(Dimension)s::Vector Vector;
    typedef typename %(Dimension)s::Tensor Tensor;
    typedef typename %(Dimension)s::SymTensor SymTensor;
    typedef typename %(Dimension)s::ThirdRankTensor ThirdRankTensor;
"""

    #...........................................................................
    # Constructors
    def pyinit(self):
        "Construct an itegrator"

    def pyinit1(self, dataBase = "DataBase<%(Dimension)s>&"):
        "Construct an integrator with a DataBase"

    def pyinit2(self,
                dataBase = "DataBase<%(Dimension)s>&",
                physicsPackages = "const std::vector<Physics<%(Dimension)s>*>&"):
        "Construct an integrator with a DataBase and physics packages"

    #...........................................................................
    # Virtual methods
    @PYB11virtual
    @PYB11const
    def label(self):
        return "std::string"

#-------------------------------------------------------------------------------
# Inject other interfaces
#-------------------------------------------------------------------------------
PYB11inject(IntegratorAbstractMethods, VerletIntegrator, pure_virtual=False, virtual=True)
