from setuptools import setup, find_packages

print(find_packages())
print("#######")
setup(
    name='cli-generator',
    version='0.1',
    description='A package wich make easier the creation of R cli wrappers',
    url='https://github.com/ebi-gene-expression-group/cli-generator',
    author='Pablo Moreno, Guilhem Marnier',
    author_email='',
    packages=find_packages(),
    license='MIT',
    install_requires=['PyYAML', 'jinja2'],

    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)