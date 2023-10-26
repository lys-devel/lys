Automated test
===============================

Before testing
--------------------
1. To execute the automated test, `lys` should be installed from source. See :doc:`../install`.

2. Install `pytest` if it is not installed::

    pip install pytest pytest-cov

3. Go to `lys` installation directory and execute automated tests::

    pytest

4. If you want to see code coverage, execute the command below::

    pytest --cov