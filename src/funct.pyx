# distutils: language = c++

from math import *
from Extension cimport Extension
from libcpp.string cimport string

cdef class PyExtension:
	cdef Extension c_ext

	def __cinit__(self, str funct, double value):
		self.c_ext = new Extension(funct, value)
	def __dealloc__(self):
		del self.c_ext

	def string_to_function(funct, value)
		formula = funct
		x = value
		result = eval(formula)
		return result;