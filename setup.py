"""Setup file for PyPi."""
from setuptools import find_packages, setup

setup(
    name='check-reserved-instances',
    license='BSD',
    description=('Compare instance reservations and running instances for AWS '
                 'services'),
    author='Terbium Labs',
    author_email='developers@terbiumlabs.com',
    url='https://github.com/TerbiumLabs/check-reserved-instances',
    keywords='ec2 elasticache rds aws reserved instances amazon web services',
    platforms=['Any'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'boto',
        'boto3',
        'click',
        'configparser',
        'Jinja2',
        'MarkupSafe',
        'python-dateutil'
    ],
    tests_require=[
        'mock',
        'pytest',
        'pytest-cov'
    ],
    entry_points={
        'console_scripts': ['check-reserved-instances = '
                            'check_reserved_instances:cli']
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ]
)
