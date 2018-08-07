from setuptools import setup, find_packages


requirements = [
    'Click>=6.0',
    'boto3>=1.5.33',
    'click-spinner>=0.1.8',
]

setup(
    name="lobo",
    version="0.0.1",
    url="https://github.com/boroivanov/lobo",

    author='Borislav Ivanov',
    author_email='borogl@gmail.com',

    description='AWS Load Balancer list cli',

    packages=find_packages(),
    install_requires=requirements,
    include_package_data=True,
    package_dir={'lobo':
                 'lobo'},
    entry_points={
        'console_scripts': [
            'lobo=lobo.main:cli'
        ]
    },

    license="MIT license",

    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
