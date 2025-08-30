from setuptools import setup, find_packages

setup(
    name="shared_utils",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "opencv-python-headless>=4.8.0",
        "numpy>=1.24.0",
        "Pillow>=10.0.0",
    ],
)
