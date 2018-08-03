#ifndef RECYCLE_SRC_PYRE_WINNING_H_
#define RECYCLE_SRC_PYRE_WINNING_H_

#include "cyclus.h"
#include "recycle_version.h"

namespace recycle {

class Winning {
public:

Winning();

Winning(winning_current, winning_time, winning_flowrate, winning_volume);
/// @param feed feed yellowcake from voloxidation
/// @param stream the separation efficiency for reduction streams
/// @return composition composition of the separated material sent to fuel fabrication
cyclus::Material::Ptr WinningSepMaterial(std::map<int, double> effs,
	cyclus::Material::Ptr mat);

double Efficiency(double current, double reprocess_time, double flowrate);

double Throughput(double reprocess_time, double volume);
};
}
#endif // RECYCLE_SRC_PYRE_WINNING_H_
