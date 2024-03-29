.. _kernelgen-app:


*********************
kernelgen app
*********************
While the Fortran Code Analysis application in Section \ref{sec:resolve} can decide which Fortran statements should be copied from the original software to the generated kernel code, we still need additional Fortran statements to make the generated kernel a stand-alone software. First, we need to provide a Fortran "PROGRAM" statement and, more importantly, statements for reading input data that drives kernel execution. This application gets the AST constructed by the "resolve" applications and manipulates the AST to be a stand-alone software. This application also converts the final AST to source files that can be compiled without errors. 

This application manipulates AST in four stages in order: "created," "process," "finalize," and "flatten." At every stage, the AST is examined and changed by the application. This staged approach allows developers to synchronize modifications made on the AST so that they can ensure some modifications are available at the next stage. Once the AST manipulation is done, the final AST is converted to Fortran source files.

In many cases of kernel extraction, preparing data input for driving kernel execution is more challenging. Especially if the application uses Fortran multi-level derived types, we need to copy data in all the levels, a.k.a "deep copy." This deep-coping is automatically accomplished by this application through instrumenting the original software. The application uses Fortran WRITE statements to save scalar variables in a binary data file. In case of array type variables, the application classifies the array variables according to Fortran "type-kind-dimension" combinations and creates binary file Input/Output (I/O) subroutines per every combination of Fortran "type-kind-dimension." The generated subroutines and their call-sites are added to the original source file. In case of derived-type, the application saves binary data for all member variables as explained previously before saving the derived type itself.

The generated data is saved in a binary file. The binary file is read in the same order in the generated kernel file using subroutines that are created similarly to the Fortran "type-kind-dimension" classification. The decision on which variables should be saved in the binary file is made by analyzing reference information generated by the "resolve" application in Section \ref{sec:resolve}.

It is crucial that the generated kernel produces the same output that the original software generates in the case that the user does not make any modifications in the extracted kernel. Therefore, the data generation application explained in the previous section also saves all output type variables in the binary file. This application reads the binary file and compares the content of variables between ones from kernel execution and the others from the original software. The comparison is done by calling subroutines that are created per every Fortran "type-kind-dimension" combination used in the code. If an output variable is a Fortran derived type, the application verifies the member variables in it one by one including member variables that are also Fortran derived types.

The generated kernel also has a feature of variable perturbation. Users optionally can pick an array input variable and slightly modify the value of its element at random. This feature is disabled initially and users can turn this feature on by un-commenting a perturbation subroutine call that is automatically generated in the kernel by this application. This feature is useful to measure the sensitivity of the kernel from varying input values. This application is invoked by using the "kernelgen" sub-command in either command-line or Python script. The application also optionally receives kernel timing data in JSON-format to decide when and how to save the variables in the binary file. Using the kernel timing data, this application selects subsets of the combinations of MPI ranks, OpenMP threads, and invocations of the kernel region.

Example
**********

Usage
**********

usage: fortlab-kernelgen [-h] [--version] [--outdir OUTDIR] [--model MODEL] [--repr-etime REPR_ETIME]
                         [--repr-papi REPR_PAPI] [--repr-code REPR_CODE]
                         analysis

positional arguments:
  analysis              analysis object

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --outdir OUTDIR       output directory
  --model MODEL         model object
  --repr-etime REPR_ETIME
                        Specifying elapsedtime representativeness feature flags
  --repr-papi REPR_PAPI
                        Specifying papi counter representativeness feature flags
  --repr-code REPR_CODE
                        Specifying code coverage representativeness feature flags

This app may feed-forward following data to next app:
  kerneldir (type=any)         kernel generation code directory
  statedir  (type=any)         state generation code directory
