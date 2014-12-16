//------------------------------------------------------------------------------
// Explicit instantiation.
//------------------------------------------------------------------------------
#include "Geometry/Dimension.hh"
#include "ConstantYVelocityBoundary.cc"

namespace Spheral {
  namespace BoundarySpace {
    template class ConstantYVelocityBoundary< Dim<2> >;
    template class ConstantYVelocityBoundary< Dim<3> >;
  }
}
