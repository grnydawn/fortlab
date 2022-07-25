
=====================
mpasocn: MPAS Ocean
=====================

Example: kernel extraction from E3SM MPAS Ocean

0. Create a E3SM case
-------------------------

First, create your E3SM case and note the path of this case directory for later use in ekea run.

1. Mark the kernel region with ekea directives in source file
----------------------------------------------------------------------------
Choose a file among MPAS Ocean source files. In this example, we marked ekea directives in components/mpas-source/src/core_ocean/shared/mpas_ocn_gm.F


#### mpas_ocn_diagnostics.F#####

.. code-block:: fortran

        module ocn_gm
        ...
        subroutine ocn_gm_compute_Bolus_velocity(diagnosticsPool, meshPool, scratchPool)
        ...   
              allocate(rightHandSide(nVertLevels))
              allocate(tridiagA(nVertLevels))
              allocate(tridiagB(nVertLevels))
              allocate(tridiagC(nVertLevels))

        !$kgen begin_callsite gm_bolus_velocity

              nCells = nCellsArray( size(nCellsArray) )
              nEdges = nEdgesArray( size(nEdgesArray) )
        ...
              !$omp do schedule(runtime)
              do iCell = 1, nCells
                 gmStreamFuncTopOfCell(:, iCell) = gmStreamFuncTopOfCell(:,iCell) / areaCell(iCell)
              end do
              !$omp end do

        !$kgen end_callsite gm_bolus_velocity
        ...
        end subroutine ocn_gm_compute_Bolus_velocity
        ...
        end module ocn_gm

2. run ekea
--------------------
Make directory for the kernel generation. Or you can specify the output directory using -o ekea option. Run ekea-mpasocn with case directory path and ekea-directed source file path.


        >>> mkdir ocn_gm_kernel
        >>> cd ocn_gm_kernel
        >>> ekea mpasocn ${HOME}/scratch/mycase ${HOME}/scratch/E3SM/components/mpas-source/src/core_ocean/shared/mpas_ocn_gm.F

ekea-mpasocn run initiates one E3SM build and two E3SM runs with additional analysis overheads. Therefore, it is advised to wait up to 2 ~ 3 times of your regular E3SM build/run time including time to wait on the job queue.

3. check extracted kernel source files and data files
---------------------------------------------------------------
Once completed kernel extraction successfully, kernel directory will be created in the output directory with source files, data files, and a Makefile. You may try to build/run the kernel as following:

 


> cd kernel
> make build
> make run
 

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
