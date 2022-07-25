.. _compileroption-app:


*********************
compileroption app
*********************



usage: fortlab-compileroption [-h] [--version] [--cleancmd CLEANCMD] [--workdir WORKDIR] [--savejson SAVEJSON]
                              [--backupdir BACKUPDIR] [--verbose] [--check]
                              build command

positional arguments:
  build command         Software build command

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --cleancmd CLEANCMD   Software clean command.
  --workdir WORKDIR     work directory
  --savejson SAVEJSON   save data in a josn-format file
  --backupdir BACKUPDIR
                        saving source files used
  --verbose             show compilation details
  --check               check strace return code

This app may feed-forward following data to next app:
  data (type=any)    json object
