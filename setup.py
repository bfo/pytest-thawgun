from setuptools import setup, find_packages

setup(
    name='pytest-thawgun',
    version='0.0.1',
    packages=find_packages(),
    url='https://github.com/mrzechonek/thawgun',
    license='Apache 2.0',
    author='Michał Lowas-Rzechonek',
    author_email='michal@rzechonek.net',
    description='Pytest plugin for time travel',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Testing",
        "Framework :: Pytest",
    ],
    python_requires='>= 3.5',
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'flask',
        'flask-restful',
        'aiohttp',
        'requests',
    ],
    install_requires=[
        'async-generator',
        'freezegun',
        'pytest-asyncio',
    ],
    entry_points={
        'pytest11': ['thawgun = pytest_thawgun.plugin']
    },
    extras_require={
        "testing": [
            "coverage",
        ],
    },
)
