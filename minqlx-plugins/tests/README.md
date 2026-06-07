# votemanager test harness

This test harness is self-contained and does not require a running Quake Live server.

Run it from the Quake-Live repository root:

```powershell
python -m unittest discover -s minqlx-plugins/tests -p "test_*.py"
```

Run only the votemanager tests:

```powershell
python -m unittest minqlx-plugins.tests.test_votemanager
```

The harness injects a small fake `minqlx` module and validates vote-start, duplicate-vote, force-vote, and kick-protection behavior in `votemanager.py`.