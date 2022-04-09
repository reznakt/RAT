from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from types import TracebackType
from typing import List, Callable, Iterator, Optional, Type, TextIO

import colorama
import tqdm
from colorama import Fore, Style

PROCESS_TIMEOUT = 1000

EXIT_CODES = {
    132: "SIGILL",
    133: "SIGTRAP",
    134: "SIGABRT",
    136: "SIGFPE",
    138: "SIGBUS",
    139: "SIGSEGV",
    158: "SIGXCPU",
    159: "SIGXFSZ"
}


class ansi_format:
    def __init__(self, *args: str, stream: TextIO = sys.stdout) -> None:
        self.codes = args
        self.stream = stream

    def __enter__(self) -> None:
        for code in self.codes:
            self.stream.write(code)

    def __exit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType]
    ) -> None:
        self.stream.write(colorama.Style.RESET_ALL)


class __RATInternalBase:
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(" \
               + ", ".join(f"{k}={repr(v)}" for k, v in self.__dict__.items()) \
               + ")"

    __repr__ = __str__


@dataclass(frozen=True)
class ProcessInput(__RATInternalBase):
    stdin: str
    argv: List[str]


@dataclass(frozen=True)
class ProcessOutput(__RATInternalBase):
    exit_code: int
    stdout: str
    stderr: str
    path: str


Comparator = Callable[[ProcessOutput, ProcessOutput], bool]
TestGenerator = Callable[[], ProcessInput]


@dataclass(frozen=True)
class TestResult(__RATInternalBase):
    test: Test
    result: bool
    exec1: ProcessOutput
    exec2: ProcessOutput


def generate_comparator(
        compare_exit_codes: bool,
        compare_stdout: bool,
        compare_stderr: bool
) -> Comparator:
    def inner(r1: ProcessOutput, r2: ProcessOutput) -> bool:
        if compare_exit_codes and r1.exit_code != r2.exit_code:
            return False
        if compare_stdout and r1.stdout != r2.stdout:
            return False
        if compare_stderr and r1.stderr != r2.stderr:
            return False
        return True

    return inner


CMP_ALL: Comparator = generate_comparator(True, True, True)
GEN_EMPTY: Callable[[], ProcessInput] = lambda: ProcessInput("", [])


class Test(__RATInternalBase):
    def __init__(
            self,
            name: str,
            __input: ProcessInput
    ) -> None:
        self.name = name
        self.input = __input

    def _execute(self, __exec: str) -> ProcessOutput:
        p = subprocess.Popen(
            f"{__exec} " + " ".join(self.input.argv),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True, text=True
        )
        stdout, stderr = p.communicate(input=self.input.stdin, timeout=PROCESS_TIMEOUT / 1000)
        rc = p.returncode if p.returncode >= 0 else 128 - p.returncode
        return ProcessOutput(rc, stdout, stderr, __exec)

    def run(self, exec1: str, exec2: str, comparator: Comparator) -> TestResult:
        r1, r2 = self._execute(exec1), self._execute(exec2)
        return TestResult(self, comparator(r1, r2), r1, r2)


class Runner:
    def __init__(
            self,
            exec1: str,
            exec2: str,
            generator: TestGenerator,
            comparator: Comparator
    ) -> None:
        self.generator = generator
        self.comparator = comparator
        self.exec1 = exec1
        self.exec2 = exec2

        for i, path in enumerate((self.exec1, self.exec2), start=1):
            if not os.path.isfile(path):
                raise ValueError(f"Invalid path exec{i}: {repr(path)}")

    def _run_test(self, test: Test) -> TestResult:
        return test.run(self.exec1, self.exec2, self.comparator)

    def iterator(self, n: int = 0) -> Iterator[TestResult]:
        i = 1
        while not n or i <= n:
            test = Test(f"test_{i}", self.generator())
            yield self._run_test(test)
            i += 1

    __iter__ = iterator

    def _run(
            self,
            n: int = 0,
            silent: bool = False,
            supress_errors: bool = False,
            verbose: bool = False,
            colors: bool = True
    ) -> bool:
        # TODO: implement silent, supress_errors, verbose and colors
        if silent or supress_errors or verbose or not colors:
            raise NotImplementedError("This feature is not implemented yet")

        if silent and verbose:
            raise ValueError("Only one of 'silent' and 'verbose' can be set to True")
        if supress_errors and not silent:
            raise ValueError("'supress_errors' can only be set with 'silent'")

        result = True

        for i, test_result in (
                pb := tqdm.tqdm(enumerate(self.iterator(n), start=1), total=n)):
            test_result: TestResult

            if not test_result.result:
                result = False
                break

        pb.close()

        if result:
            with ansi_format(Fore.GREEN, Style.BRIGHT):
                sys.stdout.write("\n\n***All tests passed***\n")
                sys.stdout.flush()
            return True

        sys.stderr.write(
            f"\n\n{Style.BRIGHT}{Fore.RED}"
            f"Falsified after {Fore.YELLOW}{i} {Fore.RED}test(s)!{Style.RESET_ALL}\n\n")

        with ansi_format(Fore.GREEN, Style.BRIGHT, stream=sys.stderr):
            sys.stderr.write("stdin: \n")
        sys.stderr.write(f"{repr(test_result.test.input.stdin)}\n\n")

        with ansi_format(Fore.GREEN, Style.BRIGHT, stream=sys.stderr):
            sys.stderr.write("args: \n")
        sys.stderr.write(f"{repr(test_result.test.input.argv)}\n\n")

        for proc in (test_result.exec1, test_result.exec2):
            sys.stderr.write("\n\n")
            with ansi_format(Fore.BLUE, Style.BRIGHT, stream=sys.stderr):
                sys.stderr.write(f"{proc.path}:\n\n")
            with ansi_format(Fore.MAGENTA, Style.BRIGHT, stream=sys.stderr):
                sys.stderr.write("exit code: ")
            with ansi_format(Fore.RED if proc.exit_code else Fore.GREEN, stream=sys.stderr):
                sys.stderr.write(f"{proc.exit_code}")
                if proc.exit_code in EXIT_CODES:
                    sys.stderr.write(f"({EXIT_CODES[proc.exit_code]})")
                sys.stderr.write("\n\n")
            with ansi_format(Fore.YELLOW, Style.BRIGHT, stream=sys.stderr):
                sys.stderr.write("stdout: \n")
            sys.stderr.write(f"{repr(proc.stdout)}\n\n")
            with ansi_format(Fore.RED, Style.BRIGHT, stream=sys.stderr):
                sys.stderr.write("stderr: \n")
            sys.stderr.write(f"{repr(proc.stderr)}\n\n")

        sys.stderr.flush()

    def run(
            self,
            n: int = 0,
            silent: bool = False,
            supress_errors: bool = False,
            verbose: bool = False,
            colors: bool = True
    ) -> bool:
        try:
            return self._run(n, silent, supress_errors, verbose, colors)
        except KeyboardInterrupt:
            raise SystemExit("Stopping...")
