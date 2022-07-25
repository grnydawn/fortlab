===============
Getting-started
===============

With FortLab, users can extract a stand-alone kernel from a Fortran program. In addition, they can create their own kernel-based analysis tool. To use it, FortLab should be installed on the system where the original Fortran program is compiled and executed.

-------------
Installation
-------------

The easiest way to install fortlab is to use the pip python package manager. 

        >>> pip install fortlab

You can install fortlab from github code repository if you want to try the latest version.

        >>> git clone https://github.com/grnydawn/fortlab.git
        >>> cd fortlab
        >>> python setup.py install

Once installed, you can test the installation by running the following command.

        >>> fortlab --version
        fortlab 0.1.15

------------
Requirements
------------

- Linux OS
- Python 3.5+
- Make building tool(make)
- C Preprocessor(cpp)
- System Call Tracer(strace)

------------------
What's in Fortlab
------------------

Fortlab is consist of multiple modules(Apps) that can be assembled together to generate a kernel-based software tools. As of this version, there are following apps in Fortlab.

* compileroption  : compiles the target application and collect compiler options per each compiled source files.
* resolve         : generates cross-referece information of all Fortran names used in the specified kernel region directly as well as indirectly.
* timinggen       : generates the elapsed time of the specified kernel region in JSON file, per every MPI ranks, every OpenMP threads(if any), and every invocation of the code regions
* kernelgen       : generates the kernel source files and data files to drive the extracted kernel.
* vargen          : generates source files that contains the cross-referece information of all Fortran names used in the specified kernel region
