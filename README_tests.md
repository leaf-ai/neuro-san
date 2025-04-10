# Running Python unit/integration tests

To run a specifc unit test

    pytest -v PathToPythonTestFile::TestClassName::TestMethodName
    pytest -v ./tests/neuro-san/internals/graph/test_sly_data_redactor.py::TestSlyDataRedactor::test_assumptions

To run all unit tests

    pytest -v ./tests

To debug a specific unit test, import pytest in the test source file

    import pytest

Set a trace to stop the debugger on the next line

    pytest.set_trace()

Run pytest with '--pdb' flag

    pytest -v --pdb ./tests/neuro-san/internals/graph/test_sly_data_redactor.py

To run all integration tests

    pytest -v ./tests -m "integration"
