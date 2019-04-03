[![Latest PyPI version](https://img.shields.io/pypi/v/lobo.svg)](https://pypi.python.org/pypi/lobo)
[![Build Status](https://travis-ci.org/boroivanov/lobo.svg)](https://travis-ci.org/boroivanov/lobo)
[![Maintainability](https://api.codeclimate.com/v1/badges/19368e2117abcea88894/maintainability)](https://codeclimate.com/github/boroivanov/lobo/maintainability)
[![Downloads](https://pepy.tech/badge/lobo)](https://pepy.tech/project/lobo)
[![Downloads](https://pepy.tech/badge/lobo/month)](https://pepy.tech/project/lobo)

# lobo
A simple cli for listing AWS load balancers and their instances/targets.

# Install
```bash
pip install lobo
```

# Usage
```bash
# List all load balancers
$ lobo

# List load balancers which match <name>
$ lobo <name>

# Pass `-s` and/or `-t` to list scheme/type.
```