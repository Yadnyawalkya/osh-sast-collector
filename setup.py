from setuptools import setup, find_packages

setup(
    name='openstack-sast-collector',
    version='1.0',
    author='Yadnyawalk Tale',
    author_email='yadnyawalkyatale@gmail.com',
    description='Openstack SAST Report Collector',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/your-username/openstack-sast-collector',
    packages=find_packages(),
    install_requires=[
        'flake8',
        'prettytable',
        'pytest', 
    ],
    extras_require={
        'dev': ['tox', 'pytest', 'flake8'],  # extras for devel
    },
    classifiers=[
        'Programming Language :: Python :: 3.10',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ], # modify, distribute and sublicense
    python_requires='>=3.6',
)
