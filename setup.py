import setuptools

setuptools.setup(
    name='mkcodes',
    install_requires=['click'],
    tests_require=['markdown'],
    extras_require={'markdown': ['markdown']},
    py_modules=['mkcodes'],
    entry_points={'console_scripts': ['mkcodes=mkcodes:main']}
)
