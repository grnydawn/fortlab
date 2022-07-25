.. _kernelgen-app:


*********************
kernelgen app
*********************

usage: fortlab-kernelgen [-h] [--version] [--outdir OUTDIR] [--model MODEL] [--repr-etime REPR_ETIME]
                         [--repr-papi REPR_PAPI] [--repr-code REPR_CODE]
                         analysis

positional arguments:
  analysis              analysis object

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --outdir OUTDIR       output directory
  --model MODEL         model object
  --repr-etime REPR_ETIME
                        Specifying elapsedtime representativeness feature flags
  --repr-papi REPR_PAPI
                        Specifying papi counter representativeness feature flags
  --repr-code REPR_CODE
                        Specifying code coverage representativeness feature flags

This app may feed-forward following data to next app:
  kerneldir (type=any)         kernel generation code directory
  statedir  (type=any)         state generation code directory
