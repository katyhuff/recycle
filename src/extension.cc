#include "pyre.h"
#include "extension.h"

namespace recycle {

	Extension::Extension() {}

	Extension::Extension(std::string string = 'x', double value = 1) {
		this->function = string;
		this->input_parameter = value;
	}
}
