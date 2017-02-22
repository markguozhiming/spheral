import mpi
from Spheral2d import *
from MedialGenerator import *
from CompositeNodeDistribution import *
from SpheralTestUtilities import *
from SpheralGnuPlotUtilities import *
from VoronoiDistributeNodes import distributeNodes2d as distributeNodes
from siloPointmeshDump import *
import numpy as np

commandLine(hmin     = 1e-5,
            hmax     = 1e1,
            rhoscale = 0.5,
            n        = 400,
            nPerh    = 2.01,
            maxIterations = 1000,
            fracTol = 1e-3,
            power    = -0.1)

#-------------------------------------------------------------------------------
# Material properties.
#-------------------------------------------------------------------------------
gamma = 1.4
mu = 2.0
eos = GammaLawGasMKS(gamma, mu)

#-------------------------------------------------------------------------------
# Interpolation kernels.
#-------------------------------------------------------------------------------
WT = TableKernel(BSplineKernel(), 1000)
output("WT")

#-------------------------------------------------------------------------------
# Make the NodeList.
#-------------------------------------------------------------------------------
nodes1 = makeFluidNodeList("nodes1", eos,
                           hmin = hmin,
                           hmax = hmax,
                           nPerh = nPerh,
                           topGridCellSize = 100,
                           xmin = Vector.one * -10.0,
                           xmax = Vector.one *  10.0)

nodeSet = [nodes1]
for nodes in nodeSet:
    output("nodes.name")
    output("  nodes.hmin")
    output("  nodes.hmax")
    output("  nodes.nodesPerSmoothingScale")

#-------------------------------------------------------------------------------
# Make the circle boundary
#-------------------------------------------------------------------------------
nc = 60
bcpoints = vector_of_Vector(nc)
bcfacets = vector_of_vector_of_unsigned(nc,vector_of_unsigned(2))
for i in xrange(nc):
    bcpoints[i] = Vector(cos(i*2.0*pi/nc),sin(i*2.0*pi/nc))
    bcfacets[i][0] = i
    bcfacets[i][1] = (i+1) % nc
outerCircle = Polygon(bcpoints,bcfacets)

#-------------------------------------------------------------------------------
# Generate them nodes.
#-------------------------------------------------------------------------------
class densityProfile:
    def __init__(self,sigma):
        self.sigma = sigma
        return
    def __call__(self,r):
        return 0.05+5.0*exp(-r**2/(2.0*self.sigma**2.0))

def integrate(densityProfileMethod,
              rmin,rmax,
              nbins = 1000):
    assert nbins > 0
    assert nbins % 2 == 0
    
    result = 0
    dr = (rmax-rmin)/nbins
    for i in xrange(1,nbins):
        r1 = rmin + (i-1)*dr
        r2 = rmin + i*dr
        result += 0.5*dr*(r2*densityProfileMethod(r2)+r1*densityProfileMethod(r1))
    result = result * (2.0*pi)
    return result

def kern(s,r):
    a = 20.0/7.0
    if (r>=2.0*s):
        return 0.0
    elif (r>s):
        return a*0.25*(2.0-r/s)**3.0
    else:
        return a*(0.25*(2.0-r/s)**3.0 - (1.0-r/s)**3.0)

def kernwall(s,r):
    a = 2.0
    b = 0.5*(log(a)-log(a/100.0))
    q = (s-r)/s
    if (q<=0.0):
        return a
    elif (q>0.0 and q<2.0):
        return a*exp(-b*q)
    else:
        return 0.0

rmax = 1.0
rho = densityProfile(0.25)

norm = integrate(rho,0,rmax)
m0   = norm/float(n)
pmax = 0

dr = rmax/1000.0
for i in xrange(1000):
    ri = dr*i
    pmax = max(rho(ri)/norm,pmax)


nc = 0
points = []
forces = []

s1 = rmax
s0 = rmax/n
pw = power
pw = pw + 1.0

'''
while (nc<n):
    x = random.uniform(-rmax,rmax)
    y = random.uniform(-rmax,rmax)
    r = sqrt(x*x+y*y)
    u = random.random()*pmax
    if (rho(r)/norm >= u and r<=rmax):
        s = sqrt(m0/rho(r))
        # give them a new position
        x = random.uniform(-rmax,rmax)
        y = random.uniform(-rmax,rmax)
        if (sqrt(x*x+y*y)<=rmax):
            points.append([x,y,s])
            forces.append([0.0,0.0])
            nc += 1
'''
while (nc < n):
    x = random.uniform(-rmax,rmax)
    y = random.uniform(-rmax,rmax)
    r = sqrt(x*x+y*y)
    if (r <= rmax):
        u = random.random()
        s = ((s1**pw - s0**pw)*u + s0**pw)**(1.0/pw)
        points.append([x,y,s])
        forces.append([0.0,0.0])
        nc += 1

ds = 0.01
dds = 1.0
k = 0

#points = np.array(points)
#np.savetxt('foo0.csv',points,delimiter=",")

while (dds > fracTol) and (k < maxIterations):
    maxs = 0.0
    for i in xrange(len(points)):
        # get point i
        xi = points[i][0]
        yi = points[i][1]
        si = points[i][2]
        # reset forces
        forces[i][0] = 0.0
        forces[i][1] = 0.0
        for j in xrange(len(points)):
            if (i!=j):
                # get point j
                xj = points[j][0]
                yj = points[j][1]
                sj = points[j][2]
                rij = sqrt((xj-xi)**2+(yj-yi)**2)
                if (rij<=2.0*(sj+si)):
                    # compute force on i from j
                    F = kern(sj,rij)
                    t = atan2(yj-yi,xj-xi)
                    Fx = F*cos(t)
                    Fy = F*sin(t)
                    forces[i][0] += -sj*Fx
                    forces[i][1] += -sj*Fy
        # add wall forces
        ri = sqrt(xi*xi+yi*yi)
        F = kernwall(rmax,ri)
        t = atan2(yi,xi)
        Fx = F*cos(t)
        Fy = F*sin(t)
        #print "[%3.3e,%3.3e] [%3.3e,%3.3e] [%3.3e,%3.3e]" % (xi,yi,-Fx,-Fy,forces[i][0],forces[i][1])
        forces[i][0] += -Fx
        forces[i][1] += -Fy
    for i in xrange(len(points)):
        # compute movement for point i
        dx = forces[i][0] * ds
        dy = forces[i][1] * ds
        x0 = points[i][0]
        y0 = points[i][1]
        
        maxs = max(maxs,sqrt(dx*dx+dy*dy))
        points[i][0] += dx
        points[i][1] += dy
        
        '''
        if (sqrt((x0+dx)**2+(y0+dy)**2)<=rmax):
            points[i][0] += dx
            points[i][1] += dy
        else:
            # need to not exceed rmax, find intersection
            x1 = x0+dx
            y1 = y0+dy
            a = (x1-x0)**2 + (y1-y0)**2
            b = 2.0*(x1-x0)*x0 + 2.0*(y1-y0)*y0
            c = x0**2 + y0**2 - rmax**2
            t = 2.0*c/(-b-sqrt(b*b-4.0*a*c))
            points[i][0] = (x1-x0)*t+x0
            points[i][1] = (y1-y0)*t+y0
            '''

    dds = maxs
    k += 1
    print k,dds

# now that the positions and sizes are fixed, fill the nodelist
nodes1.numInternalNodes = n
r = nodes1.positions()
m = nodes1.mass()
rho = nodes1.massDensity()
H = nodes1.Hfield()
for i in xrange(n):
    r[i] = Vector(points[i][0],points[i][1])
    s = points[i][2]
    m[i] = m0
    rho[i] = m0/s**2
    h = 1.0/(nPerh*s*2.0)
    H[i] = SymTensor(h,0.0,0.0,h)
    #H[i] = SymTensor(0.01,0.0,0.0,0.01)

#-------------------------------------------------------------------------------
# Construct a DataBase to hold our node list
#-------------------------------------------------------------------------------
db = DataBase()
output("db")
for nodes in nodeSet:
    db.appendNodeList(nodes)
output("db.numNodeLists")
output("db.numFluidNodeLists")

#-------------------------------------------------------------------------------
# Compute the voronoi volumes
#-------------------------------------------------------------------------------
nodes1.neighbor().updateNodes()

db.updateConnectivityMap(computeGhostConnectivity=False)
cm = db.connectivityMap()

pos = db.fluidPosition
H = db.fluidHfield
mass = db.fluidMass
rhof = db.fluidMassDensity

weight = db.newFluidScalarFieldList(0.0, "weight")

gradRhof = db.newFluidVectorFieldList(Vector.zero, "mass density gradient")
surfacePoint = db.newFluidIntFieldList(0, "surface point")
vol = db.newFluidScalarFieldList(0.0, "volume")
deltaCentroid = db.newFluidVectorFieldList(Vector.zero, "delta centroid")
A = db.newFluidScalarFieldList(0.0, "A")
B = db.newFluidVectorFieldList(Vector.zero, "B")
C = db.newFluidTensorFieldList(Tensor.zero, "B")
gradA = db.newFluidVectorFieldList(Vector.zero, "gradA")
gradB = db.newFluidTensorFieldList(Tensor.zero, "gradB")
gradC = db.newFluidThirdRankTensorFieldList(ThirdRankTensor.zero, "gradC")
m0 = db.newFluidScalarFieldList(0.0, "m0")
m1 = db.newFluidVectorFieldList(Vector.zero, "m1")
m2 = db.newFluidSymTensorFieldList(SymTensor.zero, "m2")
m3 = db.newFluidThirdRankTensorFieldList(ThirdRankTensor.zero, "m3")
m4 = db.newFluidFourthRankTensorFieldList(FourthRankTensor.zero, "m4")
gradm0 = db.newFluidVectorFieldList(Vector.zero, "gradm0")
gradm1 = db.newFluidTensorFieldList(Tensor.zero, "gradm1")
gradm2 = db.newFluidThirdRankTensorFieldList(ThirdRankTensor.zero, "gradm2")
gradm3 = db.newFluidFourthRankTensorFieldList(FourthRankTensor.zero, "gradm3")
gradm4 = db.newFluidFifthRankTensorFieldList(FifthRankTensor.zero, "gradm4")

cells = db.newFluidFacetedVolumeFieldList(FacetedVolume(), "cells")


bounds = vector_of_FacetedVolume()
bounds.append(outerCircle)
holes = vector_of_vector_of_FacetedVolume(1)

correctionOrder = 1

'''
computeCRKSPHMoments(cm, WT, vol, pos, H, correctionOrder, NodeCoupling(),
                     m0, m1, m2, m3, m4, gradm0, gradm1, gradm2, gradm3, gradm4)

print "computed moments"
'''

for i in xrange(len(weight[0])):
    weight[0][i] = points[i][2]

computeVoronoiVolume(pos, H, rhof, gradRhof, cm, WT.kernelExtent, bounds, holes,
                     surfacePoint, vol,deltaCentroid, cells)

print "computed volumes"


p = plotPolygon(outerCircle, plotVertices=False, plotLabels=False)
xmin = -1.5*Vector.one
xmax = 1.5*Vector.one
p("set size square; set xrange [%g:%g]; set yrange [%g:%g]" % (xmin.x,xmax.x,xmin.y,xmax.y))
p.refresh()
for i in xrange(len(cells[0])):
    plotPolygon(cells[0][i],plot=p,plotVertices=False,plotLabels=False)

computeWeightedVoronoiVolume(pos, H, rhof, gradRhof, cm, WT.kernelExtent, bounds, holes, weight,
                             surfacePoint, vol,deltaCentroid, cells)
                     
print "computed weighted volumes"

pp = plotPolygon(outerCircle, plotVertices=False, plotLabels=False)
xmin = -1.5*Vector.one
xmax = 1.5*Vector.one
pp("set size square; set xrange [%g:%g]; set yrange [%g:%g]" % (xmin.x,xmax.x,xmin.y,xmax.y))
pp.refresh()
for i in xrange(len(cells[0])):
    plotPolygon(cells[0][i],plot=pp,plotVertices=False,plotLabels=False)



#-------------------------------------------------------------------------------
# Drop a viz file for inspection.
#-------------------------------------------------------------------------------



Hfield = nodes1.Hfield()
HfieldInv = SymTensorField("H inverse", nodes1)
Sfield = ScalarField("Size", nodes1, 0.0)
for i in xrange(nodes1.numNodes):
    HfieldInv[i] = Hfield[i].Inverse()
    Sfield[i] = pi*(0.5*points[i][2])**2


vizfile = siloPointmeshDump(baseName = "test_medial_maxiter=%i_tol=%g" % (maxIterations, fracTol),
                            baseDirectory = "test_medial",
                            fields = ([rhof[0],pos[0],H[0],mass[0],vol[0],HfieldInv,Sfield]))
