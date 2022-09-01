rm dist/*
python -m build
python -m twine upload --repository testpypi dist/*
rm test_virtualenv/*
python -m venv ./test_virtualenv