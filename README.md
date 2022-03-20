# RAT
Welcome to RAT, a simple RAndom Testing framework.

## Installation

install:
```console
pip install git+https://github.com/sneklingame/RAT
```

update:
```console
pip install git+https://github.com/sneklingame/RAT -U
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
    exit(0 if runner.run(TESTS) else 1)
```
