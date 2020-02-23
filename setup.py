import setuptools

setuptools.setup(
    name='mkcodes',
    install_requires=['click'],
    extras_require={'markdown': ['markdown']},
    py_modules=['mkcodes'],
    entry_points={'console_scripts': ['mkcodes=mkcodes:main']}
)
