---
date: 2026-03-06T13:47:35+0000
source: https://pypi.org/project/h5py/
---
The h5py package provides both a high- and low-level interface to the HDF5
library from Python. The low-level interface is intended to be a complete
wrapping of the HDF5 API, while the high-level component supports access to
HDF5 files, datasets and groups using established Python and NumPy concepts.

A strong emphasis on automatic conversion between Python (Numpy) datatypes and
data structures and their HDF5 equivalents vastly simplifies the process of
reading and writing data from Python.

Wheels are provided for several popular platforms, with an included copy of
the HDF5 library (usually the latest version when h5py is released).

You can also build h5py from source
with any HDF5 stable release from version 1.10.4 onwards, although naturally new
HDF5 versions released after this version of h5py may not work.
Odd-numbered minor versions of HDF5 (e.g. 1.13) are experimental, and may not
be supported.
