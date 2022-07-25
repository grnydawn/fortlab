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

With FortLab, you can collect information about building and running a Fortran application or can instrument original source code to generate runtime information such as kernel timing. Following section briefly explains how FortLab works by showing an example for collectting compiler command line flags per each source files that are compiled during the application build.

--------------------------------------
Collecting compiler command-line flags
--------------------------------------

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

            !$kgen begin_callsite mykernel
            call vecadd(N, A, B, C)
            !$kgen end_callsite mykernel

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


# kernel specification


# running app

# seeing result
