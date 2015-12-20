import setuptools

setuptools.setup(
    name='mkcodes',
    install_requires=['click'],
    extras_require={'markdown': ['markdown']},
    packages=setuptools.find_packages(),
    entry_points={'console_scripts': ['mkcodes=mkcodes:main']}
)
