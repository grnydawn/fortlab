"fortlap setup module."

def main():

    from setuptools import setup, find_packages
    from fortlab.main import Fortlab as flab

    console_scripts = ["fortlab=fortlab.__main__:main"]
    install_requires = ["microapp>=0.3.15"] + flab._requires_

    setup(
        name=flab._name_,
        version=flab._version_,
        description=flab._description_,
        long_description=flab._long_description_,
        author=flab._author_,
        author_email=flab._author_email_,
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
        keywords="microapp fortlab",
        packages=find_packages(exclude=["tests"]),
        include_package_data=True,
        install_requires=install_requires,
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
