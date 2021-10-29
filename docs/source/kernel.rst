.. _kernel-index:

*****************
Marking a kernel
*****************

A user can specify the kernel region by placing two ekea comment-line directives before and after the region.


**!$kgen begin_callsite <kernel_name>**
This directive indicates that the kernel region begins after this directive. The <kernel_name> is used in the generated kernel.


**!$kgen end_callsite [kernel_name]**
This directive indicates that the kernel region ends just before this directive. The <kernel_name] is optional.


Example of directive usage
--------------------------------

.. code-block:: fortran

        !$kgen begin_callsite vecadd
        DO i=1
            C(i) = A(i) + B(i)
        END DO
        !$kgen  end_callsite
 

Notes on placing the ekea directives
--------------------------------------------

There are following limitations on placing ekea directives in source file.

        * the ekea directives should be placed within the executable constructs. For example, the directives can not be placed in specification construct such as use mpi and integer(8) i, j, k.

        * To extract a kernel that contains any communication or file system access inside, additional ekea directives should be used,  which are not documented yet.

        * the ekea directives can not be placed across block boundaries. For example, following usage is not allowed.

.. code-block:: fortran

        DO i=1
        !$kgen begin_callsite vecadd  #### NOT VALID : across DO block boundary
                C(i) = A(i) + B(i)
        END DO
        !$kgen  end_callsite #### NOT VALID : across DO block boundary 


Special notes for mpasocn
~~~~~~~~~~~~~~~~~~~~~~~~~~~

    * ekea does not support MPAS Ocean pooling mechanism. Therefore, the kernel region for extraction should not include any pooling-related code. For example, a kernel region can not include the pooling-related subroutine calls such as "mpas_pool_get_config".
    * The kernel region should not include a variable of MPAS Ocean derived data types of file_desc_t io_desc_t var_desc_t iosystem_desc_t file_desc_t io_desc_t var_desc_t iosystem_desc_t.
    * When an allocatable array or pointer variable is allocated within the kernel region, there could be an error message during kernel compilation of using the variable before being allocated. The error could be resolved by removing the line where the compilation error occurred.
