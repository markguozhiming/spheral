#ATS:test(SELF, "--linearConsistent True --graphics False", label="SVPH interpolation test -- 2-D (serial)")
#-------------------------------------------------------------------------------
# A set of tests to compare how different meshless methods interpolate fields.
#-------------------------------------------------------------------------------
from Spheral2d import *
from SpheralTestUtilities import *
from generateMesh import *
from GenerateNodeDistribution2d import *

title("SVPH Interpolation tests")

#-------------------------------------------------------------------------------
# Generic problem parameters
#-------------------------------------------------------------------------------
commandLine(
    # Parameters for seeding nodes.
    nx = 20,
    ny = 20,
    rho1 = 1.0,
    eps1 = 0.0,
    x0 = 0.0,
    x1 = 1.0,
    y0 = 0.0,
    y1 = 1.0,
    nPerh = 2.0,
    hmin = 0.0001, 
    hmax = 10.0,

    # Should we randomly perturb the positions?
    distribution = "random",
    seed = 14892042,

    # What test problem are we doing?
    testCase = "linear",

    # Should we use linearly consistent formalism?
    linearConsistent = True,
    
    # The fields we're going to interpolate.
    # Function coefficients: f(x,y) = A + B*x + C*y + D*x*y + E*x*x + F*y*y
    A = 1.0,
    B = 0.5,
    C = 2.0,
    D = 1.5,
    E = 0.25,
    F = 1.0,

    gamma = 5.0/3.0,
    mu = 1.0,

    numGridLevels = 20,
    topGridCellSize = 20.0,

    # Parameters for iterating H.
    iterateH = True,
    maxHIterations = 100,
    Htolerance = 1.0e-4,

    # Parameters for passing the test
    interpolationTolerance = 5.0e-7,
    derivativeTolerance = 5.0e-5,

    # Should we output 
    graphics = True,
    vizFileName = "SVPHInterpolation_test_viz",
    vizDir = ".",
)

assert testCase in ("constant", "linear", "quadratic")

#-------------------------------------------------------------------------------
# Which test case function are we doing?
#-------------------------------------------------------------------------------
if testCase == "constant":
    def func(pos):
        return A
    def dfunc(pos):
        return Vector(0.0, 0.0)
elif testCase == "linear":
    def func(pos):
        return A + B*pos.x + C*pos.y
    def dfunc(pos):
        return Vector(B, C)
elif testCase == "quadratic":
    def func(pos):
        return A + B*pos.x + C*pos.y + D*pos.x*pos.y + E*(pos.x)**2 + F*(pos.y)**2
    def dfunc(pos):
        return Vector(B + D*pos.y + 2.0*E*pos.x,
                      C + D*pos.x + 2.0*F*pos.y)

#-------------------------------------------------------------------------------
# Create a random number generator.
#-------------------------------------------------------------------------------
import random
rangen = random.Random()
rangen.seed(seed)

#-------------------------------------------------------------------------------
# Material properties.
#-------------------------------------------------------------------------------
eos = GammaLawGasMKS(gamma, mu)

#-------------------------------------------------------------------------------
# Interpolation kernels.
#-------------------------------------------------------------------------------
WT = TableKernel(BSplineKernel(), 1000)
output("WT")
kernelExtent = WT.kernelExtent

#-------------------------------------------------------------------------------
# Make the NodeList.
#-------------------------------------------------------------------------------
nodes1 = makeFluidNodeList("nodes1", eos,
                           hmin = hmin,
                           hmax = hmax,
                           nPerh = nPerh)
output("nodes1")
output("nodes1.hmin")
output("nodes1.hmax")
output("nodes1.nodesPerSmoothingScale")

#-------------------------------------------------------------------------------
# Set the node properties.
#-------------------------------------------------------------------------------
gen1 = GenerateNodeDistribution2d(nx, ny, rho1,
                                  distributionType = "lattice",
                                  xmin = (x0, y0),
                                  xmax = (x1, y1),
                                  nNodePerh = nPerh)

# If we're actually using a random distribution, replace the positions
# with new random sets.
if distribution == "random":
    nquant = 2**16
    usedset = set()
    i = 0
    j = rangen.randint(0, 2**32)
    dx, dy = (x1 - x0)/nquant, (y1 - y0)/nquant
    while i != nx*ny:
        while j in usedset:
            j = rangen.randint(0, 2**32)
        gen1.x[i] = x0 + (j % nquant + 0.5)*dx
        gen1.y[i] = y0 + (j // nquant + 0.5)*dy
        usedset.add(j)
        i += 1

if mpi.procs > 1:
    from VoronoiDistributeNodes import distributeNodes2d
else:
    from DistributeNodes import distributeNodes2d

distributeNodes2d((nodes1, gen1))
output("nodes1.numNodes")

# Set node specific thermal energies
nodes1.specificThermalEnergy(ScalarField("tmp", nodes1, eps1))
nodes1.massDensity(ScalarField("tmp", nodes1, rho1))

#-------------------------------------------------------------------------------
# Construct a DataBase to hold our node list
#-------------------------------------------------------------------------------
db = DataBase()
output("db")
output("db.appendNodeList(nodes1)")
output("db.numNodeLists")
output("db.numFluidNodeLists")

#-------------------------------------------------------------------------------
# Construct some boundary conditions.
#-------------------------------------------------------------------------------
bounds = vector_of_Boundary()
xbc0 = ReflectingBoundary(Plane(Vector(x0, y0), Vector( 1.0,  0.0)))
xbc1 = ReflectingBoundary(Plane(Vector(x1, y1), Vector(-1.0,  0.0)))
ybc0 = ReflectingBoundary(Plane(Vector(x0, y0), Vector( 0.0,  1.0)))
ybc1 = ReflectingBoundary(Plane(Vector(x1, y1), Vector( 0.0, -1.0)))
bounds.append(xbc0)
bounds.append(xbc1)
bounds.append(ybc0)
bounds.append(ybc1)

#-------------------------------------------------------------------------------
# Iterate the h to convergence if requested.
#-------------------------------------------------------------------------------
if iterateH:
    method = ASPHSmoothingScale()
    emptyBounds = vector_of_Boundary()
    iterateIdealH(db,
                  emptyBounds,
                  WT,
                  method,
                  maxHIterations,
                  Htolerance)

#-------------------------------------------------------------------------------
# Initialize our field.
#-------------------------------------------------------------------------------
f = ScalarField("test field", nodes1)
positions = nodes1.positions()
for i in xrange(nodes1.numInternalNodes):
    f[i] = func(positions[i])

#-------------------------------------------------------------------------------
# Build the tessellation.
#-------------------------------------------------------------------------------
mesh, void = generatePolygonalMesh([nodes1],
                                   bounds,
                                   generateVoid = False,
                                   removeBoundaryZones = False)

#-------------------------------------------------------------------------------
# Do that interpolation baby!
#-------------------------------------------------------------------------------
fl = ScalarFieldList()
fl.appendField(f)
db.updateConnectivityMap()
fSVPHfl = sampleFieldListSVPH(fl,
                              db.globalPosition,
                              db.globalHfield,
                              db.connectivityMap(),
                              WT,
                              mesh,
                              linearConsistent)
fSVPH = fSVPHfl[0]

#-------------------------------------------------------------------------------
# Prepare the answer to check against.
#-------------------------------------------------------------------------------
fans = [func(positions[i]) for i in xrange(nodes1.numInternalNodes)]
dfans = [dfunc(positions[i]) for i in xrange(nodes1.numInternalNodes)]

#-------------------------------------------------------------------------------
# Check our answers accuracy.
#-------------------------------------------------------------------------------
errfSVPH = [y - z for y, z in zip(fSVPH.internalValues(), fans)]
maxfSVPHerror = max([abs(x) for x in errfSVPH])

# errdySPH = [y - z for y, z in zip(dySPH, dyans)]
# errdySVPH = [y - z for y, z in zip(dySVPH, dyans)]
# maxdySPHerror = max([abs(x) for x in errdySPH])
# maxdySVPHerror = max([abs(x) for x in errdySVPH])

print "Maximum errors (interpolation): SVPH = %g" % (maxfSVPHerror)

#-------------------------------------------------------------------------------
# Plot the things.
#-------------------------------------------------------------------------------
if graphics:
    from SpheralVoronoiSiloDump import *
    fansField = ScalarField("answer", nodes1)
    for i in xrange(nodes1.numInternalNodes):
        fansField[i] = fans[i]
    d = SpheralVoronoiSiloDump(baseFileName = vizFileName,
                               baseDirectory = vizDir,
                               listOfFields = [fSVPH,
                                               fansField],
                               boundaries = bounds)
    d.dump(0.0, 0)

#-------------------------------------------------------------------------------
# Check the maximum SVPH error and fail the test if it's out of bounds.
#-------------------------------------------------------------------------------
if maxfSVPHerror > interpolationTolerance:
    raise ValueError, "SVPH interpolation error out of bounds: %g > %g" % (maxfSVPHerror, interpolationTolerance)
