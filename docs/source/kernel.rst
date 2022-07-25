.. _kernel-index:

===================
Kernel
===================


Marking a kernel region in a source file
==========================================

A user can specify the kernel region by placing two comment-line directives before and after the region.


**!$kgen begin_callsite <kernel_name>**
This directive indicates that the kernel region begins after this directive. The <kernel_name> is used in the generated kernel.


**!$kgen end_callsite [kernel_name]**
This directive indicates that the kernel region ends just before this directive. The <kernel_name] is optional.


Example of directive usage
==============================

.. code-block:: fortran

        !$kgen begin_callsite vecadd
        DO i=1
            C(i) = A(i) + B(i)
        END DO
        !$kgen  end_callsite
 

Notes on placing the kgen directives
==========================================

There are following limitations on placing kgen directives in source file.

        * the kgen directives should be placed within the executable constructs. For example, the directives can not be placed in specification construct such as use mpi and integer(8) i, j, k.

        * To extract a kernel that contains any communication or file system access inside, additional kgen directives should be used,  which are not documented yet.

        * the kgen directives can not be placed across block boundaries. For example, following usage is not allowed.

.. code-block:: fortran

        DO i=1
        !$kgen begin_callsite vecadd  #### NOT VALID : across DO block boundary
                C(i) = A(i) + B(i)
        END DO
        !$kgen  end_callsite #### NOT VALID : across DO block boundary 


Limitations
==========================================

    * The generated kernel should not contain any file I/O and networked I/O. In principle, there should be no side-effect in the generated kernel. 
    * Not all Fortran standards are supported. 
    * Some complext data structures such as pointers and cycled linked list are not supported. 

Extracting a kernel
==========================================

While fortran has components that collectively can extract a kernel, the actual extraction process is frequently dependent on each target application. Therefore, as an interim solution, we defer the kernel extraction to fortlab-based "applications" that are customized to the target application.

Please refer to EKEA(E3SM Kernel Extraction and Analyzer: `https://ekea.readthedocs.io <https://ekea.readthedocs.io/>`_ ) for more information on how a "fortlab application" is build.


Directories and files in kernelgen output directory
======================================================

kernel directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This directory contains kernel source files, kernel data files, a makefiles and other utility files.
The details are explained below in a seperate section.

compile.json file
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This JSON file contains compilation information of E3SM: compiler used, compiler options, MACROS defined, and temporary backup of dynamically generated files.

model.json file
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This JSON file contains kernel timing measurement information: kernel region wall-time per MPI rank, OpenMP thread, and invocation order.


backup directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This directory contains dynamically generated files.

etime directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This directory contains instrumented source files for kernel wall-time generation.

model directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This directory contains kernel timing measurments.


state directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This directory contains instrumented source files for kernel data generation.

Files in kernel directory
===============================

Kernel source files
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Files whose extension is f90. The entry of the program is in "kernel_driver.f90"

Kernel data files
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Files whose name ends with ###.###.### where # represents one or more digits. Each of these file is a set of one kernel invocation.

Makefile file
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is an auto-generated makefile to compile and run this kernel.


kgen_statefile.lst
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This file contains a name of kernel data files to be used for kernel execution. One file name is allowed per each line.



Compilation and Execution of the kernel
==============================================

Once completed kernel extraction successfully, "kernel" directory will be created in the output directory with source files, data files, and a Makefile. You may try to build/run the kernel as following:


        >>> cd kernel
        >>> make build
        >>> make run
 

The extracted kernel has a built-in timing measurement and correctness check that ensure the kernel generates the same data that the original application generates. Following is a partial capture of screen output when the gm_bolus_velocity kernel runs.

::

        ***************** Verification against 'gm_bolus_velocity.16.0.2' *****************

        Number of output variables:            43
        Number of identical variables:            43
        Number of non-identical variables within tolerance:             0
        Number of non-identical variables out of tolerance:             0
        Tolerance:    1.0000000000000000E-014

        Verification PASSED with gm_bolus_velocity.16.0.2

        gm_bolus_velocity : Time per call (usec):     47257.00000000000

        ****************************************************
        kernel execution summary: gm_bolus_velocity
        ****************************************************
        Total number of verification cases  :    42
        Number of verification-passed cases :    42

        kernel gm_bolus_velocity: PASSED verification

        number of processes  1

        Average call time (usec):  0.411E+05
        Minimum call time (usec):  0.267E+05
        Maximum call time (usec):  0.499E+05

        ****************************************************
