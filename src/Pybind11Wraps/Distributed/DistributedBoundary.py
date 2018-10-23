#-------------------------------------------------------------------------------
# DistributedBoundary
#-------------------------------------------------------------------------------
from PYB11Generator import *

from Boundary import *
from BoundaryAbstractMethods import *

@PYB11template("Dimension")
class DistributedBoundary(Boundary):

    typedefs = """
    typedef typename %(Dimension)s::Scalar Scalar;
    typedef typename %(Dimension)s::Vector Vector;
    typedef typename %(Dimension)s::Tensor Tensor;
    typedef typename %(Dimension)s::SymTensor SymTensor;
    typedef typename %(Dimension)s::ThirdRankTensor ThirdRankTensor;

    typedef std::map<int, DomainBoundaryNodes> DomainBoundaryNodeMap;
    typedef std::map<NodeList<%(Dimension)s>*, DomainBoundaryNodeMap> NodeListDomainBoundaryNodeMap;
"""

    #...........................................................................
    class DomainBoundaryNodes:
        sendNodes = PYB11readwrite()
        receiveNodes = PYB11readwrite()

    #...........................................................................
    # Constructors
    def pyinit(self):
        "Default constructor"

    #...........................................................................
    # Methods
    @PYB11const
    def communicatedNodeList(self,
                             nodeList = "const NodeList<%(Dimension)s>&"):
        "Test if the given NodeList is communicated on this domain or not."
        return "bool"

    @PYB11const
    def nodeListSharedWithDomain(self,
                                 nodeList = "const NodeList<%(Dimension)s>&",
                                 neighborDomainID = "int"):
        "Test if the given NodeList is communicated with the given domain."
        return "bool"

    @PYB11const
    @PYB11returnpolicy("reference_internal")
    def domainBoundaryNodeMap(self,
                              nodeList = "const NodeList<%(Dimension)s>&"):
        return "const DomainBoundaryNodeMap&"

    @PYB11const
    @PYB11returnpolicy("reference_internal")
    def domainBoundaryNodes(self,
                            nodeList = "const NodeList<%(Dimension)s>&",
                            neighborDomainID = "int"):
        return "const DomainBoundaryNodes&"

    @PYB11const
    def communicatedProcs(self,
                          sendProcs = "std::vector<int>&",
			  recvProcs = "std::vector<int>&"):
        "Extract the current set of processors we're communicating with."
        return "void"

    def finalizeExchanges(self):
        "Force the exchanges which have been registered to execute."
        return "void"

    def setControlAndGhostNodes(self):
        "Update the control and ghost nodes of the base class"
        return "void"

    #...........................................................................
    # Non-blocking exchanges
    @PYB11template("DataType")
    @PYB11const
    def beginExchangeField(self,
                           field = "Field<%(Dimension)s, %(DataType)s>&"):
        "Start a non-blocking Field exchange"
        return "void"

    @PYB11template("DataType")
    @PYB11const
    def beginExchangeFieldVariableSize(self,
                                       field = "Field<%(Dimension)s, %(DataType)s>&"):
        "Start a non-blocking Field exchange"
        return "void"

    beginExchangeFieldInt             = PYB11TemplateMethod(beginExchangeField, template_parameters="int", pyname="beginExchangeField")
    beginExchangeFieldScalar          = PYB11TemplateMethod(beginExchangeField, template_parameters="Scalar", pyname="beginExchangeField")
    beginExchangeFieldVector          = PYB11TemplateMethod(beginExchangeField, template_parameters="Vector", pyname="beginExchangeField")
    beginExchangeFieldTensor          = PYB11TemplateMethod(beginExchangeField, template_parameters="Tensor", pyname="beginExchangeField")
    beginExchangeFieldSymTensor       = PYB11TemplateMethod(beginExchangeField, template_parameters="SymTensor", pyname="beginExchangeField")
    beginExchangeFieldThirdRankTensor = PYB11TemplateMethod(beginExchangeField, template_parameters="ThirdRankTensor", pyname="beginExchangeField")

    beginExchangeFieldVS1             = PYB11TemplateMethod(beginExchangeFieldVariableSize, template_parameters="std::vector<Scalar>", pyname="beginExchangeFieldVariableSize")
    beginExchangeFieldVS2             = PYB11TemplateMethod(beginExchangeFieldVariableSize, template_parameters="std::vector<Vector>", pyname="beginExchangeFieldVariableSize")

    #...........................................................................
    # Virtual methods
    @PYB11pure_virtual
    def setAllGhostNodes(self,
                         dataBase = "DataBase<%(Dimension)s>&"):
        "Descendent Distributed Neighbors are required to provide the setGhostNodes method for DataBases."
        return "void"

    @PYB11virtual
    def cullGhostNodes(self,
                       flagSet = "const FieldList<%(Dimension)s, int>&",
                       old2newIndexMap = "FieldList<%(Dimension)s, int>&",
                       numNodesRemoved = "std::vector<int>&"):
        "Override the Boundary method for culling ghost nodes."
        return "void"

    @PYB11virtual
    @PYB11const
    def finalizeGhostBoundary(self):
        "Override the base method to finalize ghost boundaries."
        return "void"

    @PYB11virtual
    @PYB11const
    def meshGhostNodes(self):
        "We do not want to use the parallel ghost nodes as generators."
        return "bool"

    #...........................................................................
    # Properties
    domainID = PYB11property("int")
    numDomains = PYB11property("int")
    nodeListDomainBoundaryNodeMap = PYB11property("const NodeListDomainBoundaryNodeMap&", returnpolicy="reference_internal")

#-------------------------------------------------------------------------------
# Inject methods
#-------------------------------------------------------------------------------
PYB11inject(BoundaryAbstractMethods, DistributedBoundary, virtual=True, pure_virtual=False)
