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

.. COMMENT START
    -------------------------
    Kernel Extraction
    -------------------------

    Once fortlab is installed correctly and a E3SM case is created successfully, you can extract a kernel as explained below.

    The syntax of fortlab command is following:

            >>> fortlab <mpasocn|eam> $CASEDIR $CALLSITEFILE

    , where $CASEDIR is a directory path to E3SM case directory and $CALLSITEFILE is a file path to a E3SM source file containing fortlab kernel region directives(explained below).
    As of this version, there exist two subcommands of mpasocn and eam for MPAS Ocean Model and E3SM Atmospheric Model each. Please see _command for details about the sub-commands.

    fortlab kernel region in source code is defined by a pair of "begin_callsite" and "end_callsite" directives. The kernel region is where to be extracted. Following example shows a fortlab kernel region that encompasses a DO loop.

    ::

            !$kgen begin_callsite vecadd
            DO i=1
                    C(i) = A(i) + B(i)
            END DO
            !$kgen  end_callsite

    Please see _directives for details about using fortlab directives.
