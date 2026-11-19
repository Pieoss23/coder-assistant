# Test report

- **Esito:** failed
- **Comando:** `.\examples\flask-login\.venv\Scripts\python.exe -m unittest discover -s examples/flask-login/tests -v`
- **Return code:** `1`

## Output

```text
test_app (unittest.loader._FailedTest.test_app) ... ERROR

======================================================================
ERROR: test_app (unittest.loader._FailedTest.test_app)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_app
Traceback (most recent call last):
  File "C:\Users\ssoptr\AppData\Local\Python\pythoncore-3.14-64\Lib\unittest\loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "C:\Users\ssoptr\AppData\Local\Python\pythoncore-3.14-64\Lib\unittest\loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "C:\Progetti\SVILUPPO\coder-assistant\examples\flask-login\tests\test_app.py", line 6, in <module>
    from app import create_app
ModuleNotFoundError: No module named 'app'


----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
```
