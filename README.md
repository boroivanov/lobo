[![Latest PyPI version](https://img.shields.io/pypi/v/lobo.svg)](https://pypi.python.org/pypi/lobo)
[![Build Status](https://travis-ci.org/boroivanov/lobo.svg)](https://travis-ci.org/boroivanov/lobo)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/65b11606d2974a6592a1b15fd64d01d6)](https://www.codacy.com/project/boroivanov/lobo/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=boroivanov/lobo&amp;utm_campaign=Badge_Grade_Dashboard)
[![Maintainability](https://api.codeclimate.com/v1/badges/19368e2117abcea88894/maintainability)](https://codeclimate.com/github/boroivanov/lobo/maintainability)

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