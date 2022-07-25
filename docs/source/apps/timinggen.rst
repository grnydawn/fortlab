.. _timinggen-app:


*********************
timinggen app
*********************

::

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
