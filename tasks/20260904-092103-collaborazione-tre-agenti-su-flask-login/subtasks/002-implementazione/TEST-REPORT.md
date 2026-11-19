# Test report

- **Esito:** passed
- **Comando:** `cd /d examples\flask-login && .venv\Scripts\python.exe -m unittest discover -s tests -v`
- **Return code:** `0`

## Output

```text
test_auth_pages_expose_ui_feedback (test_app.LoginTests.test_auth_pages_expose_ui_feedback) ... ok
test_invalid_password_is_rejected (test_app.LoginTests.test_invalid_password_is_rejected) ... ok
test_logout_shows_success_feedback (test_app.LoginTests.test_logout_shows_success_feedback) ... ok
test_register_login_and_logout (test_app.LoginTests.test_register_login_and_logout) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.572s

OK
```
