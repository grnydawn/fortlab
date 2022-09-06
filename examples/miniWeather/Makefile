#NOTE: Netcdf library should be available(ex: cray-parallel-netcdf)

SIM_TIME := 10.0
OUT_FREQ := 10.0
NX := 100
NZ := 50

DATA_SPEC_COLLISION       := 1
DATA_SPEC_THERMAL         := 2
DATA_SPEC_GRAVITY_WAVES   := 3
DATA_SPEC_DENSITY_CURRENT := 5
DATA_SPEC_INJECTION       := 6

DATA_SPEC := ${DATA_SPEC_COLLISION}

FORTSRC := miniWeather_mpi.F90

FC := ftn

INCLUDES := -I${OLCF_PARALLEL_NETCDF_ROOT}/include
LIBS := -L${OLCF_PARALLEL_NETCDF_ROOT}/lib -lpnetcdf
MACROS := -D_NX=${NX} -D_NZ=${NZ} -D_SIM_TIME=${SIM_TIME} -D_OUT_FREQ=${OUT_FREQ} -D_DATA_SPEC=${DATA_SPEC}

F_FLAGS := ${INCLUDES} ${LIBS} ${MACROS} -h noacc,noomp

miniweather_fort.exe: ${FORTSRC}
	${FC} ${F_FLAGS} -o $@ $<

compileroption: clean
	fortlab compileroption "${FC} ${F_FLAGS} -c ${FORTSRC}" --savejson miniWeather_compopts.json

clean:
	rm -rf *.mod *.o *.s *.exe output.nc backup kgen.log
