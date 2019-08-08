from setuptools import setup


setup(
    name='bal',
    version='0.1',
    description='A framework for analyzing and manipulating binary data',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Red Balloon Security',
    author_email='quack-tech@redballoonsecurity.com',
    packages=[
        'bal',
        'bal.analyzers'
    ],
    include_package_data=True,
    install_requires=[
        'enum34;python_version<"3.4"',
        'typing;python_version<"3.5"',
        'six',
    ],
    extras_require={
        'docs': ['sphinx', 'sphinx-rtd-theme', 'm2r'],
        'examples': ['wget']
    }
)
