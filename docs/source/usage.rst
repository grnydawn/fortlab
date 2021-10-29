.. _usage-index:

*****************
Using a kernel
*****************

Directories and files in ekea output directory
--------------------------------------------------------

kernel directory
************************

This directory contains kernel source files, kernel data files, a makefiles and other utility files.
The details are explained below in a seperate section.

compile.json file
************************

This JSON file contains compilation information of E3SM: compiler used, compiler options, MACROS defined, and temporary backup of dynamically generated files.

model.json file
************************

This JSON file contains kernel timing measurement information: kernel region wall-time per MPI rank, OpenMP thread, and invocation order.


backup directory
************************

This directory contains dynamically generated files.

etime directory
************************

This directory contains instrumented source files for kernel wall-time generation.

model directory
************************

This directory contains kernel timing measurments.


state directory
************************

This directory contains instrumented source files for kernel data generation.


Files in kernel directory
--------------------------------------------------------

Kernel source files
************************

Files whose extension is f90. The entry of the program is in "kernel_driver.f90"

Kernel data files
************************

Files whose name ends with ###.###.### where # represents one or more digits. Each of these file is a set of one kernel invocation.

Makefile file
************************

This is an auto-generated makefile to compile and run this kernel.


kgen_statefile.lst
************************

This file contains a name of kernel data files to be used for kernel execution. One file name is allowed per each line.



Compilation and Execution of the kernel
------------------------------------------------

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
