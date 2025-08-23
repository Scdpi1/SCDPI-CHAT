from setuptools import setup, find_packages

setup(
    name="scdpi-chat",
    version="2.1.0",
    author="SCDPI Team",
    author_email="scdpi@protonmail.com",
    description="Cliente IRC com notificações e modo interativo",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["requests", "cryptography"],
    entry_points={
        'console_scripts': [
            'scdpi-chat=scdpi_chat:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
