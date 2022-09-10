.. _timinggen-app:


*********************
timinggen app
*********************

This app instruments the original code to insert timing generation code. The timing collection measures the elapsed time between the beginning and the end of the specified kernel region per every execution from all threads and processes. For example, in case of MPI and OpenMP enabled software, the total number of measurements is the product of the number of invocations, the number of OpenMP threads, and the number of MPI ranks.

Example
************

To explain Fortlab compileroption app, we will use `Fortran MPI version of miniWeather <https://github.com/mrnorman/miniWeather/blob/main/fortran/miniWeather_mpi.F90>`_ as introduced in :ref:`builtin-apps` section.

To collect timing data from compilation of miniWeather.F90, we ran following fortlab command with timinggen subcommand. Following shows the command line that compiles miniWeather in a Makefile. You can find the entire code of the Makefile at `https://github.com/grnydawn/fortlab/blob/master/examples/miniWeather/Makefile <https://github.com/grnydawn/fortlab/blob/master/examples/miniWeather/Makefile>`_.

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

Before running fortlab command, we need to specify where to measure the timing in the source code. In this example, we specified the region for timing generation in the subroutine of compute_tendencies_z as shown below.

.. code-block:: fortran

        !$kgen begin_callsite tend_z

            !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            !! TODO: THREAD ME
            !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            !Compute fluxes in the x-direction for each cell
            do k = 1 , nz+1
              do i = 1 , nx
                !Use fourth-order interpolation from four cell averages to compute the value at the interface in question
                do ll = 1 , NUM_VARS
                  do s = 1 , sten_size
                    stencil(s) = state(i,k-hs-1+s,ll)
                  enddo
                  !Fourth-order-accurate interpolation of the state
                  vals(ll) = -stencil(1)/12 + 7*stencil(2)/12 + 7*stencil(3)/12 - stencil(4)/12
                  !First-order-accurate interpolation of the third spatial derivative of the state
                  d3_vals(ll) = -stencil(1) + 3*stencil(2) - 3*stencil(3) + stencil(4)
                enddo

                !Compute density, u-wind, w-wind, potential temperature, and pressure (r,u,w,t,p respectively)
                r = vals(ID_DENS) + hy_dens_int(k)
                u = vals(ID_UMOM) / r
                w = vals(ID_WMOM) / r
                t = ( vals(ID_RHOT) + hy_dens_theta_int(k) ) / r
                p = C0*(r*t)**gamma - hy_pressure_int(k)
                !Enforce vertical boundary condition and exact mass conservation
                if (k == 1 .or. k == nz+1) then
                  w                = 0
                  d3_vals(ID_DENS) = 0
                endif

                !Compute the flux vector with hyperviscosity
                flux(i,k,ID_DENS) = r*w     - hv_coef*d3_vals(ID_DENS)
                flux(i,k,ID_UMOM) = r*w*u   - hv_coef*d3_vals(ID_UMOM)
                flux(i,k,ID_WMOM) = r*w*w+p - hv_coef*d3_vals(ID_WMOM)
                flux(i,k,ID_RHOT) = r*w*t   - hv_coef*d3_vals(ID_RHOT)
              enddo
            enddo

        !$kgen end_callsite

There are two ekea directives: begin_callsite and end_callsite. The code block between the two directives is the kernel block. "!$kgen" marks that the rest of the line is ekea directive. "tend_z" gives the specified code block of the kernel name.


Following Linux shell command runs Fortlab compileroption app.

.. code-block:: bash

        fortlab timinggen "make miniWeather_fort.exe" --savejson miniWeather_compopts.json

"fortlab" is a main command to drive its subcommands. In above example, "compileroption" sub-command is used to collect compiler flags. The actual command for compilation is shown inside of double-quotation marks. The compiler flags can be collected from child processes. For example, this example uses a Makefile. You can optionally save the result to Json file using "--savejson" sub option.

Once the above command runs with success, "miniWeather_compopts.json" file will be created. The content of the json file is shown below.

.. code-block:: json
   :linenos:

        {"etime": {
          "23": {
            "0": {
              "1": ["3.21706E+03", "3.21707E+03"],
              "2": ["3.21709E+03", "3.21710E+03"],
              "3":...
            }...
          }...
         }...
        }

Listing 10 shows the JSON content of "timinggen” app output. Line 1 shows the type of this JSON object. In this 12
13 means the MPI rank that the timing output is generated 14
case,thetypeiselapsedtime.Thenumber"23"inline2
from. Similarly, "0" in line 3 is the OpenMP thread number. The key values in line 4-6, means the order of invocations that the kernel region is executed. The array values of each invocation are timestamps of the beginning and the end of the kernel execution.

The timing data is used to choose the best combinations of "invocation-OpenMP thread-MPI rank" that produces the kernel driving data whose timing statistics efficiently match to the statistics from the execution of the original software.

It receives a AST generated by "resolve" app. After instrumenting the code, the app compiles and runs the instrumented software to generate raw timing data, and finally it merges the timing raw data in an JSON-format file.

Usage
************

usage: fortlab-timinggen [-h] [--version] [--cleancmd CLEANCMD] [--buildcmd build command] [--runcmd run command]
                                 [--outdir OUTDIR] [--no-cache]
                                 analysis

        positional arguments:
          analysis              analysis object

        optional arguments:
          -h, --help            show this help message and exit
          --version             show program's version number and exit
          --cleancmd CLEANCMD   Software clean command.
          --buildcmd build command
                                Software build command
          --runcmd run command  Software run command
          --outdir OUTDIR       output directory
          --no-cache            force to collect timing data

        This app may feed-forward following data to next app:
          etimedir (type=any)        elapsedtime instrumented code directory
          modeldir (type=any)        elapsedtime data directory
