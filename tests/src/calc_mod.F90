MODULE calc_mod

    enum , bind(c)
      enumerator :: One = 1 
      enumerator :: Two
      enumerator :: Three
    end enum

    PUBLIC calc
CONTAINS
    SUBROUTINE calc(i, j, output, out2, out3)
        IMPLICIT NONE
        INTEGER, INTENT(IN) :: i, j
        real, INTENT(OUT), dimension(:,:) :: out3, output, out2

          ! Also a comment
        !$kgen coverage test1
        IF ( i > j ) THEN
            output(i,j) = i - j + REAL(One)
            out2(i, j) = 2*(i-j) + REAL(Two)
            out3(i, j) = 3*(i-j) + REAL(Three)
        !$kgen coverage test2
        ELSE
            output(i,j) = j - i
            out2(i, j) = 2*(j-i)
            out3(i, j) = 3*(j-i)
        END IF
        SELECT CASE (i)
        CASE (0)
            output(i,1) = i - j
        CASE (1)
            output(i,1) = i - j
        CASE (2)
            output(i,1) = i - j
        CASE (3)
            output(i,1) = i - j
        CASE DEFAULT
            output(i,1) = i - j
        END SELECT
    END SUBROUTINE
END MODULE
