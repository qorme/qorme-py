from typing import Any

class TracebackEntry:
    filename: str
    func_name: str
    line: str
    lineno: int

    def __init__(self, filename: str, func_name: str, line: str, lineno: int) -> None: ...

def get_line(filename: str, lineno: int) -> str: ...

class Traceback:
    def __init__(self, config: Any) -> None: ...
    def get_stack(self) -> list[TracebackEntry]: ...
