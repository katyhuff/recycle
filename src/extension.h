#ifndef RECYCLE_SRC_EXTENSION_H_
#define RECYCLE_SRC_EXTENSION_H_

#include "recycle_version.h"

namespace recycle {

class Extension {

public:

// default constructor
Extension();

// overloaded constructor
Extension(std::string funct, double value);

std::string fucnt;
double value;

}
#endif // RECYCLE_SRC_EXTENSION_H_