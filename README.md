# RAT
Welcome to RAT, a simple RAndom Testing framework.

## Installation

install:
```console
pip install git+https://github.com/reznakt/RAT
```

upgrade:
```console
pip install --upgrade --no-deps --force-reinstall git+https://github.com/reznakt/RAT
```

## Usage
```python
from rat import Runner, ProcessInput, generate_comparator


def generate_input():
    ...


if __name__ == '__main__':
    runner = Runner(
        "path/to/exec1",
        "path/to/exec2",
        lambda: ProcessInput(generate_input(), ["--flag"]),
        generate_comparator(
            compare_exit_codes=True, 
            compare_stdout=True, 
            compare_stderr=True
        )
    )
    exit(0 if runner.run() else 1)
```
