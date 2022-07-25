.. fortlab documentation master file, created by
   sphinx-quickstart on Wed Mar 10 14:45:17 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. only:: html

    :Release: |release|
    :Date: |today|

========
FortLab 
========

Welcome to the Kernel Extraction and Tool Development Framework for Fortran Applications.

FortLab is a python framework on that users can create a kernel extraction and analysis tools for Fortran applications. Kernel is a software extracted from a large original software as a stand-alone program. In general, kernel is easier to use than its original software due to its reduced size and complexity. In addition to kernel extraction, FortLab exposes key capabilities related to kernel extraction and analysis: 1) Fortran Source Code Analysis, 2) Compiler option collection, 3) Source code modification, and 4) Data generation for kernel execution. Therefore, FortLab users can create their own tool based on the capabilities. 


FortLab documentation: `https://fortlab.readthedocs.io <https://fortlab.readthedocs.io/>`_

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   intro
   overview
   apps/index
   examples/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
