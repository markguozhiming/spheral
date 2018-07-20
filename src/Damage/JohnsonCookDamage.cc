//---------------------------------Spheral++----------------------------------//
// JohnsonCookDamage -- an implementation of a Johnson-Cook damage law.
//
// Created by JMO, Mon Jul  9 08:21:23 PDT 2018
//----------------------------------------------------------------------------//
#include "FileIO/FileIO.hh"
#include "JohnsonCookDamage.hh"
#include "JohnsonCookFailureStrainPolicy.hh"
#include "JohnsonCookDamagePolicy.hh"
#include "EffectiveTensorDamagePolicy.hh"
#include "Strength/SolidFieldNames.hh"
#include "Strength/MeltEnergyPolicy.hh"
#include "NodeList/SolidNodeList.hh"
#include "DataBase/DataBase.hh"
#include "DataBase/State.hh"
#include "DataBase/StateDerivatives.hh"
#include "Hydro/HydroFieldNames.hh"
#include "Field/FieldList.hh"
#include "Boundary/Boundary.hh"
#include "Neighbor/Neighbor.hh"
#include "Utilities/globalNodeIDs.hh"
#include "Utilities/mortonOrderIndices.hh"
#include "Utilities/nodeOrdering.hh"

#include <string>
#include <vector>
#include <algorithm>
#include <random>
#include <unordered_map>

namespace Spheral {
namespace PhysicsSpace {

using namespace std;

using NodeSpace::NodeList;
using NodeSpace::SolidNodeList;
using Material::EquationOfState;
using FileIOSpace::FileIO;
using DataBaseSpace::DataBase;
using FieldSpace::Field;
using FieldSpace::FieldList;
using BoundarySpace::Boundary;
using NeighborSpace::ConnectivityMap;
using KernelSpace::TableKernel;
using NeighborSpace::Neighbor;

//------------------------------------------------------------------------------
// Constructor.
//------------------------------------------------------------------------------
template<typename Dimension>
JohnsonCookDamage<Dimension>::
JohnsonCookDamage(SolidNodeList<Dimension>& nodeList,
                  const double D1,
                  const double D2,
                  const double D3,
                  const double D4,
                  const double D5,
                  const double aD1,
                  const double bD1,
                  const double eps0D1,
                  const double aD2,
                  const double bD2,
                  const double eps0D2,
                  const double epsilondot0,
                  const double Tcrit,
                  const double sigmamax,
                  const double efailmin,
                  const unsigned seed,
                  const bool domainIndependent):
  mNodeList(nodeList),
  mD1("D1_" + nodeList.name(), nodeList, D1),
  mD2("D2_" + nodeList.name(), nodeList, D2),
  mFailureStrain(SolidFieldNames::flaws, nodeList),
  mMeltSpecificEnergy(SolidFieldNames::meltSpecificEnergy, nodeList),
  mNewEffectiveDamage(EffectiveTensorDamagePolicy<Dimension>::prefix() + SolidFieldNames::effectiveTensorDamage, nodeList),
  mD3(D3),
  mD4(D4),
  mD5(D5),
  mepsilondot0(epsilondot0),
  mTcrit(Tcrit),
  msigmamax(sigmamax),
  mefailmin(efailmin),
  mRestart(DataOutput::registerWithRestart(*this)) {
  
  // We need to generate the D1 and D2 Fields Weibull distributed fields.
  // If the a value is 0.0, we take this to mean the corresponding D coefficient is constant.
  if (aD1 != 0.0 or aD2 != 0.0) {

    // Are we generating domain-independent?
    if (domainIndependent) {

      // Construct a random number generator.
      // C++11 provides a Weibull distribution natively.
      std::mt19937 gen(seed);
      std::weibull_distribution<> d1(aD1, bD1), d2(aD2, bD2);

      // First, assign a unique ordering to the nodes so we can step through them
      // in a domain independent manner.
      typedef KeyTraits::Key Key;
      DataBase<Dimension> db;
      db.appendNodeList(nodeList);
      auto keyList = mortonOrderIndices(db);
      auto orderingList = nodeOrdering(keyList);
      CHECK(orderingList.numFields() == 1);
      auto& ordering = *orderingList[0];
      const auto n = std::max(0, ordering.max());  // Note this is the global number of nodes.

      // Reverse lookup in the ordering.
      unordered_map<unsigned, unsigned> order2local;
      for (auto i = 0; i != nodeList.numInternalNodes(); ++i) order2local[ordering[i]] = i;

      // Walk the global number of node in Morton order.
      for (auto iorder = 0; iorder < n + 1; ++iorder) {

        // Is this one of our nodes?
        auto itr = order2local.find(iorder);
        if (itr != order2local.end()) {

          // This node is on this domain, so assign D1 and D2.
          const auto i = itr->second;
          CHECK(i < nodeList.numInternalNodes());
          if (aD1 != 0.0) mD1[i] = D1*(d1(gen) + eps0D1);
          if (aD2 != 0.0) mD2[i] = D2*(d2(gen) + eps0D2);

        } else {

          // Otherwise we just spin the random generators to keep all domains in sync.
          d1(gen);
          d2(gen);

        }
      }

    } else {
    
      // In the non-domain independent case we can generate more quickly in parallel.
      // Construct a random number generator.
      // C++11 provides a Weibull distribution natively.
      const auto procID = Process::getRank();
      std::mt19937 gen((seed + procID)*(seed + procID + 1)/2 + procID);
      std::weibull_distribution<> d1(aD1, bD1), d2(aD2, bD2);

      // Walk the global number of node in Morton order.
      const auto n = nodeList.numInternalNodes();
      for (auto i = 0; i < n; ++i) {
        if (aD1 != 0.0) mD1[i] = D1*(d1(gen) + eps0D1);
        if (aD2 != 0.0) mD2[i] = D2*(d2(gen) + eps0D2);
      }
    }
  }

  cout << "D1: " << mD1 << endl;
  cout << "D2: " << mD2 << endl;
}

//------------------------------------------------------------------------------
// Destructor.
//------------------------------------------------------------------------------
template<typename Dimension>
JohnsonCookDamage<Dimension>::
~JohnsonCookDamage() {
}

//------------------------------------------------------------------------------
// Increment the derivatives.
//------------------------------------------------------------------------------
template<typename Dimension>
void
JohnsonCookDamage<Dimension>::
evaluateDerivatives(const Scalar time,
                    const Scalar dt,
                    const DataBaseSpace::DataBase<Dimension>& dataBase,
                    const State<Dimension>& state,
                    StateDerivatives<Dimension>& derivs) const {

  // Fow now we update the effective damage as simply a copy of the damage.
  const auto& D = state.field(state.buildFieldKey(SolidFieldNames::tensorDamage, mNodeList.name()), SymTensor::zero);
  auto& Deff = derivs.field(state.buildFieldKey(EffectiveTensorDamagePolicy<Dimension>::prefix() + SolidFieldNames::effectiveTensorDamage, mNodeList.name()), SymTensor::zero);
  Deff = D;
}

//------------------------------------------------------------------------------
// Vote on a time step.
//------------------------------------------------------------------------------
template<typename Dimension>
typename JohnsonCookDamage<Dimension>::TimeStepType
JohnsonCookDamage<Dimension>::
dt(const DataBaseSpace::DataBase<Dimension>& dataBase, 
   const State<Dimension>& state,
   const StateDerivatives<Dimension>& derivs,
   const Scalar currentTime) const {
  return TimeStepType(1.0e100, "Rate of damage change -- NO VOTE.");
}

//------------------------------------------------------------------------------
// Register the state and update policies.
//------------------------------------------------------------------------------
template<typename Dimension>
void
JohnsonCookDamage<Dimension>::
registerState(DataBase<Dimension>& dataBase,
              State<Dimension>& state) {

  typedef typename State<Dimension>::PolicyPointer PolicyPointer;

  // Register the failure strains for updating.
  PolicyPointer flawPolicy(new JohnsonCookFailureStrainPolicy<Dimension>(mD1,
                                                                         mD2,
                                                                         mD3,
                                                                         mD4,
                                                                         mD5,
                                                                         mepsilondot0,
                                                                         msigmamax,
                                                                         mefailmin,
                                                                         mTcrit));
  state.enroll(mFailureStrain, flawPolicy);

  // Register the damage and effective damage.
  PolicyPointer damagePolicy(new JohnsonCookDamagePolicy<Dimension>());
  PolicyPointer effDamagePolicy(new EffectiveTensorDamagePolicy<Dimension>());
  state.enroll(mNodeList.damage(), damagePolicy);
  state.enroll(mNodeList.effectiveDamage(), effDamagePolicy);

  // We also require the melt energy.
  PolicyPointer meltPolicy(new MeltEnergyPolicy<Dimension>());
  state.enroll(mMeltSpecificEnergy, meltPolicy);
}

//------------------------------------------------------------------------------
// Register the derivatives.
//------------------------------------------------------------------------------
template<typename Dimension>
void
JohnsonCookDamage<Dimension>::
registerDerivatives(DataBase<Dimension>& dataBase,
                    StateDerivatives<Dimension>& derivs) {
  derivs.enroll(mNewEffectiveDamage);
}

//------------------------------------------------------------------------------
// Apply the boundary conditions to the ghost nodes.
//------------------------------------------------------------------------------
template<typename Dimension>
void
JohnsonCookDamage<Dimension>::
applyGhostBoundaries(State<Dimension>& state,
                     StateDerivatives<Dimension>& derivs) {

  // Grab this models damage field from the state.
  typedef typename State<Dimension>::KeyType Key;
  const Key nodeListName = this->nodeList().name();
  const Key DKey = state.buildFieldKey(SolidFieldNames::tensorDamage, nodeListName);
  const Key DeffKey = state.buildFieldKey(SolidFieldNames::effectiveTensorDamage, nodeListName);
  CHECK(state.registered(DKey));
  CHECK(state.registered(DeffKey));
  auto& D = state.field(DKey, SymTensor::zero);
  auto& Deff = state.field(DeffKey, SymTensor::zero);

  // Apply ghost boundaries to the damage.
  for (ConstBoundaryIterator boundaryItr = this->boundaryBegin();
       boundaryItr != this->boundaryEnd();
       ++boundaryItr) {
    (*boundaryItr)->applyGhostBoundary(D);
    (*boundaryItr)->applyGhostBoundary(Deff);
  }
}

//------------------------------------------------------------------------------
// Enforce boundary conditions for the physics specific fields.
//------------------------------------------------------------------------------
template<typename Dimension>
void
JohnsonCookDamage<Dimension>::
enforceBoundaries(State<Dimension>& state,
                  StateDerivatives<Dimension>& derivs) {

  // Grab this models damage field from the state.
  typedef typename State<Dimension>::KeyType Key;
  const Key nodeListName = this->nodeList().name();
  const Key DKey = state.buildFieldKey(SolidFieldNames::tensorDamage, nodeListName);
  const Key DeffKey = state.buildFieldKey(SolidFieldNames::effectiveTensorDamage, nodeListName);
  const Key gradDKey = state.buildFieldKey(SolidFieldNames::damageGradient, nodeListName);
  CHECK(state.registered(DKey));
  CHECK(state.registered(DeffKey));
  CHECK(state.registered(gradDKey));
  auto& D = state.field(DKey, SymTensor::zero);
  auto& Deff = state.field(DeffKey, SymTensor::zero);
  auto& gradD = state.field(gradDKey, Vector::zero);

  // Enforce!
  for (ConstBoundaryIterator boundaryItr = this->boundaryBegin(); 
       boundaryItr != this->boundaryEnd();
       ++boundaryItr) {
    (*boundaryItr)->enforceBoundary(D);
    (*boundaryItr)->enforceBoundary(Deff);
  }
}

//------------------------------------------------------------------------------
// Dump the current state to the given file.
//------------------------------------------------------------------------------
template<typename Dimension>
void
JohnsonCookDamage<Dimension>::
dumpState(FileIO& file, const string& pathName) const {
  file.write(mD1, pathName + "/D1");
  file.write(mD2, pathName + "/D2");
  file.write(mFailureStrain, pathName + "/failureStrain");
  file.write(mMeltSpecificEnergy, pathName + "/meltSpecificEnergy");
}

//------------------------------------------------------------------------------
// Restore the state from the given file.
//------------------------------------------------------------------------------
template<typename Dimension>
void
JohnsonCookDamage<Dimension>::
restoreState(const FileIO& file, const string& pathName) {
  file.read(mD1, pathName + "/D1");
  file.read(mD2, pathName + "/D2");
  file.read(mFailureStrain, pathName + "/failureStrain");
  file.read(mMeltSpecificEnergy, pathName + "/meltSpecificEnergy");
}

}
}
