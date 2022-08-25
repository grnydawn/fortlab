.. _apps-index:

=================================
Apps
=================================


Fortlab is consist of multiple applications that can be assembled together to generate a kernel-based software tools. As of this version, there are following apps in Fortlab.

* compileroption  : compiles the target application and collect compiler options per each compiled source files.
* resolve         : generates cross-referece information of all Fortran names used in the specified kernel region directly as well as indirectly.
* timinggen       : generates the elapsed time of the specified kernel region in JSON file, per every MPI ranks, every OpenMP threads(if any), and every invocation of the code regions
* kernelgen       : generates the kernel source files and data files to drive the extracted kernel.
* vargen          : generates source files that contains the cross-referece information of all Fortran names used in the specified kernel region



.. toctree::
    :maxdepth: 2

    compileroption
    resolve
    timinggen
    kernelgen
    vargen
