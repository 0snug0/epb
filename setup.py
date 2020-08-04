import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="epb-0snug0", # Replace with your own username
    version="0.0.1",
    author="Eric Lugo",
    author_email="eric.lugo@sysdig.com",
    description="An easy way to build the probes",
    url="https://github.com/0snug0/epb",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)