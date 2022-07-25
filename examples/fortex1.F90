program hello 
    integer, parameter :: N = 10
    integer, dimension(N) :: A, B, C
    integer :: i

    do i=1,N
       A(i) = 1
       B(i) = 2
       C(i) = 0
    end do

    !$kgen begin_callsite vecacc
    call vecadd(N, A, B, C)
    !$kgen end_callsite vecacc

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
