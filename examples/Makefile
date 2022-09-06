
COMPILE_COMMAND := "gfortran -O3 -DNELEMS=10 fortex1.F90"

ex1:
	fortlab compileroption ${COMPILE_COMMAND} --savejson mykernel.json

clean:
	rm -rf a.out kgen.log backup *.json 
