//---------------------------------Spheral++----------------------------------//
// globalNodeIDs (contains numGlobalNodes and globalNodeIDs)
//
// Helper methods to assign unique global node IDs to all node in a NodeList,
// serial or parallel.  *Should* compute the same unique ID for each node no
// matter how the parallel domains are carved up.  
//
// Note this is accomplished by sorting based on position, so nodes occupying
// the same position are considered degenerate and may get different IDs for
// different decompositions.
//
// Created by JMO, Fri Oct 29 13:08:33 2004
//----------------------------------------------------------------------------//
#include <vector>

#include "boost/tuple/tuple.hpp"
#include "boost/tuple/tuple_comparison.hpp"
#ifdef USE_MPI
#include "mpi.h"
#include "Distributed/Communicator.hh"
#endif

#include "NodeList/NodeList.hh"
#include "Field/Field.hh"
#include "Field/FieldList.hh"
#include "DataBase/DataBase.hh"
#include "DBC.hh"

namespace Spheral {
namespace NodeSpace {

//------------------------------------------------------------------------------
// Return the total global number of nodes in the NodeList.
//------------------------------------------------------------------------------
template<typename Dimension>
inline
int
numGlobalNodes(const NodeList<Dimension>& nodeList) {
  int localResult = nodeList.numInternalNodes();
#ifdef USE_MPI
  int result;
  MPI_Allreduce(&localResult, &result, 1, MPI_INT, MPI_SUM, Communicator::communicator());
  CHECK(result >= localResult);
#else
  const int result = localResult;
#endif
  return result;
}
  
//------------------------------------------------------------------------------
// Return the total global number of nodes in the DataBase.
//------------------------------------------------------------------------------
template<typename Dimension>
inline
int
numGlobalNodes(const DataBaseSpace::DataBase<Dimension>& dataBase) {
  return numGlobalNodes<Dimension, typename DataBaseSpace::DataBase<Dimension>::ConstNodeListIterator>(dataBase.nodeListBegin(), dataBase.nodeListEnd());
}

//------------------------------------------------------------------------------
// Return the total global number of nodes in the set of NodeLists.
//------------------------------------------------------------------------------
template<typename Dimension, typename NodeListIterator>
inline
int
numGlobalNodes(const NodeListIterator& begin,
               const NodeListIterator& end) {
  int result = 0;
  for (NodeListIterator nodeListItr = begin; nodeListItr != end; ++nodeListItr) {
    result += numGlobalNodes(**nodeListItr);
  }
  return result;
}
  
//------------------------------------------------------------------------------
// Compute a unique set of global node IDs for the given NodeList, and return
// the set of them on this process.
//------------------------------------------------------------------------------
template<typename Dimension>
inline
FieldSpace::Field<Dimension, int>
globalNodeIDs(const NodeList<Dimension>& nodeList) {

  using namespace std;
  using FieldSpace::Field;
  typedef typename Dimension::Vector Vector;

  // Get the local domain ID and number of processors.
  int procID = 0;
  int numProcs = 1;
#ifdef USE_MPI
  MPI_Comm_rank(Communicator::communicator(), &procID);
  MPI_Comm_size(Communicator::communicator(), &numProcs);
#endif

  // Get the position field for this NodeList.
  int numLocalNodes = nodeList.numInternalNodes();
  const FieldSpace::Field<Dimension, Vector>& r = nodeList.positions();

  // Build the local list of node info.
  typedef std::vector<boost::tuples::tuple<Vector, int, int> > InfoType;
  InfoType nodeInfo;
  for (int i = 0; i != numLocalNodes; ++i) {
    nodeInfo.push_back(boost::tuples::tuple<Vector, int, int>(r(i), i, procID));
  }

  // Reduce the list of node info to processor 0.
  int numGlobalNodes = numLocalNodes;
#ifdef USE_MPI
  if (procID == 0) {

    // Process 0 receives and builds the global info.
    for (int recvDomain = 1; recvDomain != numProcs; ++recvDomain) {
      MPI_Status status;
      int numRecvNodes;
      MPI_Recv(&numRecvNodes, 1, MPI_INT, recvDomain, 10, Communicator::communicator(), &status);
      CHECK(numRecvNodes >= 0);
      numGlobalNodes += numRecvNodes;
      std::vector<double> packedPositions(numRecvNodes*Dimension::nDim);
      std::vector<int> packedLocalIDs(numRecvNodes);
      MPI_Recv(&(*packedPositions.begin()), numRecvNodes*Dimension::nDim, MPI_DOUBLE,
               recvDomain, 11, Communicator::communicator(), &status);
      MPI_Recv(&(*packedLocalIDs.begin()), numRecvNodes, MPI_INT,
               recvDomain, 12, Communicator::communicator(), &status);
      int offset = 0;
      for (int i = 0; i != numRecvNodes; ++i) {
        Vector ri;
        for (int j = 0; j != Dimension::nDim; ++j) {
          CHECK(offset + j < packedPositions.size());
          ri(j) = packedPositions[offset + j];
        }
        offset += Dimension::nDim;
        nodeInfo.push_back(boost::tuples::tuple<Vector, int, int>(ri, packedLocalIDs[i], recvDomain));
      }
    }

  } else {
             
    // Send our local info to processor 0.
    std::vector<double> packedPositions;
    std::vector<int> packedLocalIDs;
    for (typename InfoType::const_iterator itr = nodeInfo.begin();
         itr != nodeInfo.end();
         ++itr) {
      for (typename Vector::const_iterator ritr = boost::tuples::get<0>(*itr).begin();
           ritr != boost::tuples::get<0>(*itr).end();
           ++ritr) {
        packedPositions.push_back(*ritr);
      }
      packedLocalIDs.push_back(boost::tuples::get<1>(*itr));
    }
    CHECK(packedPositions.size() == nodeInfo.size() * Dimension::nDim);
    CHECK(packedLocalIDs.size() == nodeInfo.size());

    MPI_Send(&numLocalNodes, 1, MPI_INT, 0, 10, Communicator::communicator());
    MPI_Send(&(*packedPositions.begin()), numLocalNodes*Dimension::nDim,
             MPI_DOUBLE, 0, 11, Communicator::communicator());
    MPI_Send(&(*packedLocalIDs.begin()), numLocalNodes,
             MPI_INT, 0, 12, Communicator::communicator());

  }
#endif
  CHECK(nodeInfo.size() == numGlobalNodes);

  // Sort the node info.
  if (nodeInfo.size() > 0) {
    sort(nodeInfo.begin(), nodeInfo.end());
    BEGIN_CONTRACT_SCOPE;
    for (int i = 0; i < nodeInfo.size() - 1; ++i) {
      CHECK(boost::tuples::get<0>(nodeInfo[i]) <= boost::tuples::get<0>(nodeInfo[i + 1]));
    }
    END_CONTRACT_SCOPE;
  }

  // Now we can assign consecutive global IDs based on the sorted list.
  std::vector< std::vector<int> > globalIDs(numProcs);
  for (int i = 0; i != nodeInfo.size(); ++i) {
    const int recvProc = boost::tuples::get<2>(nodeInfo[i]);
    const int localID = boost::tuples::get<1>(nodeInfo[i]);
    CHECK(recvProc < globalIDs.size());
    if (localID + 1 > globalIDs[recvProc].size()) globalIDs[recvProc].resize(localID + 1);
    globalIDs[recvProc][localID] = i;
  }

  // Assign process 0's Ids.
  FieldSpace::Field<Dimension, int> result("global IDs", nodeList);
  if (procID == 0) {
    for (int i = 0; i != numLocalNodes; ++i) result(i) = globalIDs[0][i];
  }

#ifdef USE_MPI
  // Farm the ID info back to all processors.
  if (procID == 0) {

    // Process 0 sends the info.
    for (int recvProc = 1; recvProc != numProcs; ++recvProc) {
      int numRecvNodes = globalIDs[recvProc].size();
      MPI_Send(&numRecvNodes, 1, MPI_INT, recvProc, 20, Communicator::communicator());
      MPI_Send(&(*globalIDs[recvProc].begin()), numRecvNodes, MPI_INT,
               recvProc, 21, Communicator::communicator());
    }

  } else {

    // Get our ids from process 0.
    MPI_Status status;
    int numRecvNodes;
    MPI_Recv(&numRecvNodes, 1, MPI_INT, 0, 20, Communicator::communicator(), &status);
    CHECK(numRecvNodes == numLocalNodes);
    MPI_Recv(&(*result.begin()), numRecvNodes, MPI_INT, 0, 21, Communicator::communicator(),
             &status);

  }
#endif

  // We're done.
  return result;
}

//------------------------------------------------------------------------------
// Compute a unique set of global node IDs for all nodes across all NodeLists in
// a DataBase, returning the result as a FieldList<int>.
//------------------------------------------------------------------------------
template<typename Dimension>
// inline
FieldSpace::FieldList<Dimension, int>
globalNodeIDs(const DataBaseSpace::DataBase<Dimension>& dataBase) {
  return globalNodeIDs<Dimension, typename DataBaseSpace::DataBase<Dimension>::ConstNodeListIterator>(dataBase.nodeListBegin(), dataBase.nodeListEnd());
}

//------------------------------------------------------------------------------
// Compute a unique set of global node IDs for all nodes in the given set of
// NodeLists, returning the result as a FieldList<int>.
//------------------------------------------------------------------------------
template<typename Dimension, typename NodeListIterator>
// inline
FieldSpace::FieldList<Dimension, int>
globalNodeIDs(const NodeListIterator& begin,
              const NodeListIterator& end) {

  // Prepare the result.
  const size_t numNodeLists = std::distance(begin, end);
  FieldSpace::FieldList<Dimension, int> result(FieldSpace::FieldList<Dimension, int>::Copy);
  for (NodeListIterator itr = begin; itr != end; ++itr) {
    result.appendField(FieldSpace::Field<Dimension, int>("global IDs", **itr));
  }
  CHECK(result.numFields() == numNodeLists);

#ifdef USE_MPI
  // This processors domain id.
  int procID, numProcs;
  MPI_Comm_rank(Communicator::communicator(), &procID);
  MPI_Comm_size(Communicator::communicator(), &numProcs);

  // Count up how many nodes are on this domain.
  int numDomainNodes = 0;
  for (NodeListIterator nodeListItr = begin; nodeListItr != end; ++nodeListItr)
    numDomainNodes += (*nodeListItr)->numInternalNodes();

  // Now loop over each processor, and have each send the cumulative number
  // on to the next.
  int beginID = 0;
  for (int sendProc = 0; sendProc < numProcs - 1; ++sendProc) {
    int sendProcDomainNodes = numDomainNodes;
    MPI_Bcast(&sendProcDomainNodes, 1, MPI_INT, sendProc, Communicator::communicator());
    if (procID > sendProc) beginID += sendProcDomainNodes;
  }
  const int endID = beginID + numDomainNodes;

  // Now assign global IDs to each node on this domain in the DataBase.
  // Loop over each NodeList in the DataBase.
  int nodeListID = 0;
  for (NodeListIterator nodeListItr = begin; nodeListItr != end; ++nodeListItr, ++nodeListID) {
    const NodeList<Dimension>& nodeList = **nodeListItr;
    FieldSpace::Field<Dimension, int>& globalIDs = **result.fieldForNodeList(nodeList);

    // Construct the set of global IDs for this NodeList on this domain.
    CHECK(endID - beginID >= nodeList.numInternalNodes());
    for (int i = 0; i != nodeList.numInternalNodes(); ++i) globalIDs(i) = beginID + i;
    beginID += nodeList.numInternalNodes();
  }
  CHECK(beginID == endID);

  // Post-conditions.
  BEGIN_CONTRACT_SCOPE;
  {
    ENSURE(result.numFields() == numNodeLists);

    // Make sure each global ID is unique.
    const int nGlobal = numGlobalNodes<Dimension, NodeListIterator>(begin, end);
    for (int checkProc = 0; checkProc != numProcs; ++checkProc) {
      for (typename FieldSpace::FieldList<Dimension, int>::const_iterator fieldItr = result.begin();
           fieldItr != result.end();
           ++fieldItr) {
        int n = (*fieldItr)->nodeListPtr()->numInternalNodes();
        typename FieldSpace::Field<Dimension, int>::const_iterator fieldBegin = (*fieldItr)->begin();
        typename FieldSpace::Field<Dimension, int>::const_iterator fieldEnd = fieldBegin + n;
        MPI_Bcast(&n, 1, MPI_INT, checkProc, Communicator::communicator());
        for (int i = 0; i != n; ++i) {
          int id;
          if (procID == checkProc) id = (**fieldItr)(i);
          MPI_Bcast(&id, 1, MPI_INT, checkProc, Communicator::communicator());
          ENSURE(i >= 0 && i < nGlobal);
          if (procID != checkProc)
            ENSURE(find(fieldBegin, fieldEnd, id) == fieldEnd);
        }
      }
    }
  }
  END_CONTRACT_SCOPE;

#else

  // Provide a serial version (pretty simple mindedly).
  int numCumulativeNodes = 0;
  for (NodeListIterator nodeListItr = begin; nodeListItr != end; ++nodeListItr) {
    const NodeList<Dimension>& nodeList = **nodeListItr;
    FieldSpace::Field<Dimension, int>& globalIDs = **result.fieldForNodeList(nodeList);
    globalIDs = globalNodeIDs(nodeList);
    for (int i = 0; i != globalIDs.numElements(); ++i) globalIDs(i) += numCumulativeNodes;
    numCumulativeNodes += globalIDs.numElements();
  }

#endif

  // That's it.
  return result;
}

}
}
