#ifndef RECYCLE_SRC_PYRE_REFINING_H_
#define RECYCLE_SRC_PYRE_REFINING_H_

#include "cyclus.h"
#include "recycle_version.h"

namespace recycle {

class Refine{

public:

// default constructor
Refine();

// overloaded constructor
Refine(double refine_temp, double refine_press, double refine_rotation, 
	   double refine_batch_size, double refine_time);

/// @param feed salt with uranium and fission product feed
/// @param stream the separation efficiency for reduction streams
/// @return composition composition of the separated material sent to electrowinning
cyclus::Material::Ptr RefineSepMaterial(std::map<int, double> effs,
	cyclus::Material::Ptr mat);

private:

double temp;
double pressure;
double rotation;
double batch_size;
double reprocess_time;

/// @param temp temperature in the refining vessel
/// @param pressure pressure in the refining vessel
/// @param rotation stirrer rotation speed
/// @return efficiency separation efficiency of the refining process
double Efficiency(double temp, double pressure, double rotation);

/// @param batch_size size of separation batch
/// @param reprocess_time time spent in the refining vessel
/// @return throughput throughput of the refining subprocess
double Throughput(double batch_size, double reprocess_time);
};
}
#endif // RECYCLE_SRC_PYRE_REFINING_H_
