.. _vargen-app:


*********************
vargen app
*********************

This application generates variable and function (subroutine) cross-reference information and puts the information within the source code as comment lines where the variable or function is defined as well as used. By having the information next to the variables or functions that are defined or used in the source file, users can easily navigate source codes for analysis. This cross-reference information could be useful in case it is hard to get such analysis information from a tool such as Integrated Development Environment.

The application can analyze the following information: 1) module variables used in functions, 2) caller sites for functions, 3) local variables used in the kernel block, 4) module variables used within the kernel block, and 5) code locations where module variables are referenced.

This application can be invoked as shown at the top of Figure \ref{fig:ekea-varwhere}, similarly to the kernel extraction application explained in Section \ref{sec:ekeaextract}. This application has almost the same operations seen in Section \ref{fig:ekea-extract} except that the kernel generation part is not used. In this application, kernel source files are also created containing Fortran name cross-reference information in comment lines.


.. code-block:: fortran
   :linenos:


        !Local variables possibly modified
        !groupitr : derived
        ...
        !Local variables possibly used as operand
        !temperatureshortwavetendency : implicit array
        ...
        !External variables possibly modified
        !hnewinv : at module ocn_tracer_advection_mono
        ...
        !External variables possibly used as operand
        !redidiffon : at module ocn_vmix_coefs_redi
        ...
        !!! START OF KERNEL REGION
        ...
        !!! END OF KERNEL REGION


In Listing \ref{lst:varwhere-output}, the comment lines contain the application-generated cross-reference information. The comment lines are written just before the kernel region where the user has specified for analysis. To reduce the amount of information, only one variable per one analysis case is shown in Listing \ref{lst:varwhere-output}. The analysis information in the comment lines are only relevant to the kernel region. For example, "groupitr" variable shown in Line 2, is a local-scope variable in the kernel region, and the comment line 1 tells that "groupitr" is possibly modified in the kernel region. In line 5, we can see that "temperatureshortwavetendency" variable is used in a Fortran statement. The analysis also applies to module variables. In line 8, the analysis tells that "hnewinv" variable may be modified during the execution of this kernel region. and Line 11 tells that "redidiffon" variable may be used in the kernel execution as an operand. To save the space, we have not shown the cross-reference analysis for function caller-callee relations.

Example
************



Usage
***********
usage: fortlab-vargen [-h] [--version] [--outdir OUTDIR] analysis

positional arguments:
  analysis         analysis object

optional arguments:
  -h, --help       show this help message and exit
  --version        show program's version number and exit
  --outdir OUTDIR  output directory

This app may feed-forward following data to next app:
  kerneldir (type=any)         kernel generation code directory
