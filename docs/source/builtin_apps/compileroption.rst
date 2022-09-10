.. _compileroption-app:


*********************
compileroption app
*********************

Compiler options are important information to understand how a program source code is translated to a binary code. For example, macros in compiler command-line are used for many large applications. In addition, using the exact compiler options that are used to compile the original software is crucial to improve the representativeness of the generated kernel.

FortLab uses Linux "strace" tool that traces system calls and signals. FortLab executes a Linux command that builds the original software under "strace" and parses the output from strace by tracing "execve" system call. The "strace" com- mand and options used in the app are shown in Listing 9. As a result of this app, developers can get all macro defi- nitions and include paths per every source file used in the compilation. A JSON file can be generated from this app so that developers can use it for later use. For example, "re- solve" app in Section 2.4.1 reads this JSON file through the "--compiler-info" option.



.. code-block:: bash
   :linenos:


    >> strace −f −s 100000 −e trace=execve −q −v −− /bin/sh −c "compile−command"

"compile-command" is where to put the command-line string for compiling the original software. The "-e" option of "strace" sets to collect only "execve" system calls that are used by compiler invocations.

Example
*********

To explain Fortlab compileroption app, we will use `Fortran MPI version of miniWeather <https://github.com/mrnorman/miniWeather/blob/main/fortran/miniWeather_mpi.F90>`_ as introduced in :ref:`builtin-apps` section.

To collect compiler flags from compilation of miniWeather.F90, we ran following fortlab command with compileroption subcommand. Following shows the command line that compiles miniWeather in a Makefile. You can find the entire code of the Makefile at `https://github.com/grnydawn/fortlab/blob/master/examples/miniWeather/Makefile <https://github.com/grnydawn/fortlab/blob/master/examples/miniWeather/Makefile>`_.

.. code-block:: makefile

        INCLUDES := -I...
        LIBS := -L...
        MACROS := -D_NX=${NX} -D_NZ=${NZ} -D_SIM_TIME=${SIM_TIME} \
                  -D_OUT_FREQ=${OUT_FREQ} -D_DATA_SPEC=${DATA_SPEC}

        FORTSRC := miniWeather_mpi.F90
        F_FLAGS := ${INCLUDES} ${LIBS} ${MACROS} -h noacc,noomp
        FC := ftn

        miniweather_fort.exe: ${FORTSRC}
            ${FC} ${F_FLAGS} -o $@ $<

Following Linux shell command runs Fortlab compileroption app.

.. code-block:: bash

        fortlab compileroption "make miniWeather_fort.exe" --savejson miniWeather_compopts.json

"fortlab" is a main command to drive its subcommands. In above example, "compileroption" sub-command is used to collect compiler flags. The actual command for compilation is shown inside of double-quotation marks. The compiler flags can be collected from child processes. For example, this example uses a Makefile. You can optionally save the result to Json file using "--savejson" sub option.

Once the above command runs with success, "miniWeather_compopts.json" file will be created. The content of the json file is shown below.

.. code-block:: json

        {
            "/.../fortlab/examples/miniWeather/miniWeather_mpi.F90": {
                "compiler": "/opt/cray/pe/craype/2.7.15/bin/ftn",
                "include": [
                    "/include"
                ],
                "macros": [
                    [
                        "_NX",
                        "100"
                    ],
                    [
                        "_NZ",
                        "50"
                    ],
                    [
                        "_SIM_TIME",
                        "10.0"
                    ],
                    [
                        "_OUT_FREQ",
                        "10.0"
                    ],
                    [
                        "_DATA_SPEC",
                        "1"
                    ]
                ],
                "openmp": [],
                "options": [
                    "-h",
                    "noacc,noomp"
                ],
                "srcbackup": [
                    "/.../fortlab/examples/miniWeather/backup/src/0"
                ]
            }
        }

As you can see the details of compiler and compiler options are saved in Json file. "srcbackup" is a list of backup copies of the source files used during the compilation. This feature may be needed in the case that a build system dynamically generates and deletes source files at compile time. The information in this Json file may be further used for another applicationp. In case of kernel extraction, the information in this Json file is used to analyze source files with proper include paths and macro definitions.

Usage
*******

compileroption app is invoked as a subcommand of fortlab command. You may first check the usage of fortlab command explained in a :ref:`overview section <fortlab_command_usage>` if you are not familiar with fortlab command.

usage: fortlab-compileroption [-h] [--version] [--cleancmd CLEANCMD] [--workdir WORKDIR] [--savejson SAVEJSON] [--backupdir BACKUPDIR] [--verbose] [--check] build command

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
  data (type=any)    The collected compiler options can be used as an input data to next Fortlab app without saving as a file. If an app is linked as a next app of this compileroption app, the linked app can use the compiler flags with an input argument name of "data".
