# RAT
Welcome to RAT, a simple RAndom Testing framework.

## Installation

install:
```console
pip install git+https://github.com/sneklingame/RAT
```

upgrade:
```console
pip install --upgrade --no-deps --force-reinstall git+https://github.com/sneklingame/RAT
```

## Usage
```python
from rat import Runner, ProcessInput, CMP_ALL


def generate_input():
    ...


if __name__ == '__main__':
    runner = Runner(
        "path/to/exec1",
        "path/to/exec2",
        lambda: ProcessInput(generate_input(), ["--flag"]),
        CMP_ALL
    )
    exit(0 if runner.run() else 1)
```
