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
- Compiler(s) to compile your Fortran application



----------------------------------------------------
Using Fortlab built-in apps
----------------------------------------------------

With FortLab, you can collect information about building and running a Fortran application or can instrument original source code to generate runtime information such as kernel timing. This section briefly explains how FortLab works by showing an example of collecting compiler command line flags per each source files that are compiled during the application build ("compileroption").

"compileroption" app collects compiler flags from any build system including Makefile, Cmake, or any custom build system.

To demonstrate, we created a simple Makefile that runs gfortran shown below. However, you can change the content of Makefile including compiler command to fit your needs:

**<Makefile>**

.. code-block:: make

        compile:
	        gfortran -O3 -DNELEMS=10 fortex1.F90

Following Linux command runs fortlab with compileroption app to collect compiler flags from running above Makefile. It is assumed that fortlab is installed on the system as explained above.

**<fortlab Linux command>**

.. code-block:: bash

        >> fortlab compileroption "make compile" --savejson compopts.json

Following json file is generated from running the compileroption app.


**<compopts.json>**

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

"srcbackup" is a list of backup copies of the source files used during the compilation. This feature may be needed in the case that a build system dynamically generates and deletes source files at compile time.

To see more examples that uses other FortLab apps, please see :ref:`builtin-apps`.

----------------------------------------------------
Building and running a custom Fortlab apps
----------------------------------------------------

You can create and run your own Fortlab app by optionally using one or more Fortlab builtin apps. Please see :ref:`custom-apps` for more details.

