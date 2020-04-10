"fortlap setup module."

def main():

    from setuptools import setup

    console_scripts = ["fortlab=fortlab.__main__:main"]

    setup(
        name="fortlab",
        version="0.1.0",
        description="Fortran Laboratory",
        long_description="Tools for Analysis of Fortran Application and Source code",
        author="Youngsung Kim",
        author_email="youngsung.kim.act2@gmail.com",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Science/Research",
            "Topic :: Scientific/Engineering",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
        ],
        keywords="fortlab",
        packages=[ "fortlab" ],
        include_package_data=True,
        install_requires=["twine"],
        entry_points={ "console_scripts": console_scripts,
            "microapp.projects": "fortlab = fortlab"},
        project_urls={
            "Bug Reports": "https://github.com/grnydawn/fortlab/issues",
            "Source": "https://github.com/grnydawn/fortlab",
        }
    )

if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
