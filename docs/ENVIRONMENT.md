# Environment

The supported environment is Python 3.10+ with `qiskit==2.5.2` and
`sympy==1.14.0`, installed from `requirements.txt` or the project metadata.
Use a dedicated virtual environment (for example `D:\venvs\qrewrite`) and
run commands from outside the Qiskit source checkout when validating the wheel.

The Qiskit checkout at `D:\Desktop_Files\qiskit` is not a runtime dependency
and is never added to `PYTHONPATH`. On Windows, a source build may require
MSVC `link.exe`; the installed wheel avoids that requirement.
