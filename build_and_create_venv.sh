rm dist/*
python3 -m build
python3 -m twine upload --repository testpypi dist/*
rm test_virtualenv/*
python3 -m venv ./test_virtualenv
source ./test_virtualenv/bin/activate
python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps pygame_chess_api
python -m pip install pygame