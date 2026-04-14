import functools


class GzipCompressor:
    __slots__ = ("compress",)

    def __init__(self, level: int):
        try:
            from isal.igzip import compress
        except ImportError:
            from gzip import compress

            # Scale since gzip levels are from 1 to 9.
            level = 1 + level * 2

        self.compress = functools.partial(compress, compresslevel=level)
