#ifndef RECYCLE_SRC_PYRE_WINNING_H_
#define RECYCLE_SRC_PYRE_WINNING_H_

#include "cyclus.h"
#include "recycle_version.h"

namespace recycle {


class Winning {

public:

// default constructor
Winning();

// overloaded constructor
Winning(double winning_current, double winning_time, double winning_flowrate, double winning_volume);

/// @param feed feed yellowcake from voloxidation
/// @param stream the separation efficiency for electrowinning streams
/// @return composition composition of the separated material sent to fuel fabrication
cyclus::Material::Ptr WinningSepMaterial(std::map<int, double> effs,
	cyclus::Material::Ptr mat);

private:

double current;
double reprocess_time;
double flowrate;
double volume;

/// @param current current passed through the anode
/// @param reprocess_time time spent in electrowinning
/// @param flowrate material flowrate through the chamber
/// @return efficiency separation efficiency of the electrowinning process
double Efficiency(double current, double reprocess_time, double flowrate);

/// @param reprocess_time time spent in the winning chamber
/// @param volume size of the winning chamber
/// @return throughput product throughput of electrowinning
double Throughput(double reprocess_time, double volume);
};
}
#endif // RECYCLE_SRC_PYRE_WINNING_H_
