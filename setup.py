
import setuptools

with open('requirements.txt') as f:
    INSTALL_REQUIRES = f.read().strip().split('\n')

with open("README.md", "r", encoding="utf-8") as fh:
    LONG_DESCRIPTION = fh.read()


setuptools.setup(
    name = 'matoconv',
    description = 'Matoconv provides a reliable API to convert HTML to docx/PDF and other formats.',
    url = 'https://gitlab.dockstudios.co.uk/pub/matoconv',
    keywords = 'python convert docx pdf odt libreoffice',
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author = 'Matt Comben',
    author_email = 'matthew@dockstudios.co.uk',
    version = '3.0.0',
    license = 'GNU GPLv3',
    install_requires = INSTALL_REQUIRES,
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    scripts=['matoconv/server.py'],
    packages=['matoconv'],
    test_suite='nose.collector',
    tests_require=['nose'],
    include_package_data=True,
)
