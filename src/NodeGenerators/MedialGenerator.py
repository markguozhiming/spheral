from math import *
import mpi

from NodeGeneratorBase import *
from Spheral import Vector2d, Tensor2d, SymTensor2d, \
     rotationMatrix2d, testPointInBox2d

from sobol import i4_sobol
from centroidalRelaxNodes import centroidalRelaxNodes

#-------------------------------------------------------------------------------
# 2D Generator.  Seeds positions within the given boundary using the Sobol 
# sequence to create the seeds.
#-------------------------------------------------------------------------------
class MedialGenerator2d(NodeGeneratorBase):

    #---------------------------------------------------------------------------
    # Constructor.
    #---------------------------------------------------------------------------
    def __init__(self,
                 n,
                 rho,
                 boundary,
                 gradrho = None,
                 holes = [],
                 maxIterations = 100,
                 fracTol = 1.0e-3,
                 tessellationFileName = None,
                 nNodePerh = 2.01,
                 offset = (0.0, 0.0),
                 rejecter = None):

        assert n > 0
        assert len(holes) == 0   # Not supported yet, but we'll get there.

        # Load our handy 2D aliases.
        import Spheral2d as sph

        # Did we get passed a function or a constant for the density?
        if type(rho) == type(1.0):
            def rhofunc(posi):
                return rho
        else:
            rhofunc = rho
        self.rhofunc = rhofunc

        # Create a temporary NodeList we'll use store and update positions.
        eos = sph.GammaLawGasMKS(2.0, 2.0)
        WT = sph.TableKernel(sph.NBSplineKernel(7), 1000)
        nodes = sph.makeFluidNodeList("tmp generator nodes", 
                                      eos,
                                      hmin = 1e-10,
                                      hmax = 1e10,
                                      kernelExtent = 1.0,
                                      hminratio = WT.kernelExtent,
                                      nPerh = nNodePerh)

        # Initialize the desired number of generators in the boundary using the Sobol sequence.
        pos = nodes.positions()
        mass = nodes.mass()
        rho = nodes.massDensity()
        nodes.numInternalNodes = n
        length = max(boundary.xmax.x - boundary.xmin.x,
                     boundary.xmax.y - boundary.xmin.y)
        area = boundary.volume
        seed = 0
        i = 0
        while i < n:
            [coords, seed] = i4_sobol(2, seed)
            p = boundary.xmin + length*Vector2d(coords[0], coords[1])
            ihole = 0
            use = boundary.contains(p, False)
            if use:
                while use and ihole < len(holes):
                    use = not holes[ihole].contains(p, True)
            if use:
                pos[i] = p
                rho[i] = rhofunc(p)
                mass[i] = rho[i] * area/n
                i += 1

        # Iterate the points toward centroidal relaxation.
        vol, surfacePoint = centroidalRelaxNodes([(nodes, boundary)],
                                                 W = WT,
                                                 rho = rhofunc,
                                                 #gradrho = gradrho,
                                                 tessellationFileName = tessellationFileName)

        # Now we can fill out the usual Spheral generator info.
        self.x, self.y, self.m, self.H = [], [], [], []
        for i in xrange(n):
            self.x.append(pos[i].x)
            self.y.append(pos[i].y)
            self.m.append(vol(0,i) * rhofunc(pos[i]))
            hi = nNodePerh * sqrt(vol(0,i)/pi)
            assert hi > 0.0
            self.H.append(SymTensor2d(1.0/hi, 0.0, 0.0, 1.0/hi))
        assert len(self.x) == n
        assert len(self.y) == n
        assert len(self.m) == n
        assert len(self.H) == n

        # If the user provided a "rejecter", give it a pass
        # at the nodes.
        if rejecter:
            self.x, self.y, self.m, self.H = rejecter(self.x,
                                                      self.y,
                                                      self.m,
                                                      self.H)

        # Have the base class break up the serial node distribution
        # for parallel cases.
        NodeGeneratorBase.__init__(self, True,
                                   self.x, self.y, self.m, self.H)
        return

    #---------------------------------------------------------------------------
    # Get the position for the given node index.
    #---------------------------------------------------------------------------
    def localPosition(self, i):
        assert i >= 0 and i < len(self.x)
        assert len(self.x) == len(self.y)
        return Vector2d(self.x[i], self.y[i])
    
    #---------------------------------------------------------------------------
    # Get the mass for the given node index.
    #---------------------------------------------------------------------------
    def localMass(self, i):
        assert i >= 0 and i < len(self.m)
        return self.m[i]
    
    #---------------------------------------------------------------------------
    # Get the mass density for the given node index.
    #---------------------------------------------------------------------------
    def localMassDensity(self, i):
        assert i >= 0 and i < len(self.H)
        return self.rhofunc(Vector2d(self.x[i], self.y[i]))
    
    #---------------------------------------------------------------------------
    # Get the H tensor for the given node index.
    #---------------------------------------------------------------------------
    def localHtensor(self, i):
        assert i >= 0 and i < len(self.H)
        return self.H[i]
