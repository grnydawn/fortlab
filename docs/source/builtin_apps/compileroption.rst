.. _compileroption-app:


*********************
compileroption app
*********************

Many compiler options dictate which part of code should be com- piled and how the binary code should be generated. For example, it is common practice to use macros to specify a re- gion of code to be compiled in large applications. In addition, using the exact compiler options that are used to compile the original software is crucial to improve the representativeness of the generated kernel.

FortLab uses Linux "strace" tool that traces system calls and signals. FortLab executes a Linux command that builds the original software under "strace" and parses the output from strace by tracing "execve" system call. The "strace" com- mand and options used in the app are shown in Listing 9. As a result of this app, developers can get all macro defi- nitions and include paths per every source file used in the compilation. A JSON file can be generated from this app so that developers can use it for later use. For example, "re- solve" app in Section 2.4.1 reads this JSON file through the "--compiler-info" option.



.. code-block:: bash
   :linenos:


    >> strace −f −s 100000 −e trace=execve \
       −q −v −− /bin/sh −c "compile−command"

"compile-command" is where to put the command-line string for compiling the original software. The "-e" option of "strace" sets to collect only "execve" system calls that are used by compiler invocations.

Example
*********

To explain, we will use following simple Fortran application that adds two vector element-wise.

.. code-block:: fortran

        program hello
            integer, parameter :: N = 10
            integer, dimension(N) :: A, B, C
            integer :: i

            do i=1,N
               A(i) = 1
               B(i) = 2
               C(i) = 0
            end do

            call vecadd(N, A, B, C)

            do i=1,N
               if (C(i) .ne. 3) then
                   print *, "mismatch"
                   stop
               end if
            end do

            print *, "correct"

        contains

            subroutine vecadd(N, A, B, C)
                integer, intent(in) :: N
                integer, dimension(:), intent(in) :: A, B
                integer, dimension(:), intent(out) :: C
                integer :: i

                do i=1,N
                    C(i) = A(i) + B(i)
                end do

            end subroutine

        end program

Fortlab distribution comes with several built-in apps that collectively expose kernel extraction capability. One of them is to collect compiler flags for each of all compiled source files. In this example, we will show how to use the Fortlab app("compileroption") for collecting compiler flags.

To collect compiler flags, we ran following fortlab command with compileroption subcommand in bash shell.

.. code-block:: bash

        fortlab compileroption "gfortran -O3 -DNELEMS=10 fortex1.F90" --savejson mykernel.json

"fortlab" is a main command to drive its subcommands. In above example, "compileroption" sub-command is used to collect compiler flags. The compiler flags can be collected from child processes. For example, user can use shell scripts, or Makefiles, or any other build-system that may embed compiler invocation deep in its code. Next argument to fortlab-compileroption command is the compiling command itself. You can optionally save the result to Json file using "--savejson" sub option.

Once the above command comples with success, "mykernel.json" file will be created. The content of "mykernel.json" is shown below.

.. code-block:: json

        {
            "/autofs/nccs-svm1_home1/grnydawn/repos/github/fortlab/examples/fortex1.F90": {
                "compiler": "/usr/bin/gfortran",
                "include": [],
                "macros": [
                    [
                        "NELEMS",
                        "10"
                    ]
                ],
                "openmp": [],
                "options": [
                    "-O3"
                ],
                "srcbackup": [
                    "/autofs/nccs-svm1_home1/grnydawn/repos/github/fortlab/examples/backup/src/0"
                ]
            }
        }


As you can see the details of compiler and compiler options are saved in Json file. The information in this Json file may be further used for another applicationp. In case of kernel extraction, the information in this Json file is used to analyze source files with proper include paths and macro definitions.

Usage
*******

compileroption app is invoked as a subcommand of fortlab command. You may first check the usage of fortlab command explained in a :ref:`overview section <fortlab_command_usage>` if you are not familiar with fortlab command.

usage: fortlab-compileroption [-h] [--version] [--cleancmd CLEANCMD] [--workdir WORKDIR] [--savejson SAVEJSON]
                              [--backupdir BACKUPDIR] [--verbose] [--check]
                              build command

positional arguments:
  build command         Software build command

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --cleancmd CLEANCMD   CLEANCMD is a Linux shell command that clear all the object and other intermittent files. You may wrap the command with double or single qutation marks if there exist spaces in the command.
  --workdir WORKDIR     Any output files will be crated in WORKDIR
  --savejson SAVEJSON   Collected compiler options will be saved in a JOSN file of SAVEJSON
  --backupdir BACKUPDIR
                        To support the case that a build-system generates new source files during the build phase but delete before completing compilation, this app saves all the source files used in the build in BACKUPDIR
  --verbose             show compilation details
  --check               check strace return code

This app may feed-forward following data to next app:
  data (type=any)    The collected compiler options can be used as an input data to next Fortlab app without saving as a file. If an app linked as a next app, the app can use the compiler flags with an input argument name of "data".
