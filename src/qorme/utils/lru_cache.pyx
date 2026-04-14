from cpython.dict cimport PyDict_Next
from cpython.object cimport PyObject


cdef class LRUCache(dict):
    """
    LRU cache implementation that leverages the fact that
    `dict` objects preserve insertion order (since Python 3.7).
    """

    def __cinit__(self, int maxsize=256):
        self.maxsize = maxsize

    cpdef get(self, key): 
        if (value := self.pop(key, None)) is not None:
            # Insert it back so it's the 'last' key.
            self[key] = value
            return value

    cpdef void set(self, key, value):
        cdef:
            PyObject *lru_key
            Py_ssize_t pos = 0

        if len(self) == self.maxsize:
            # Remove the 'first' key.
            PyDict_Next(self, &pos, &lru_key, NULL)
            del self[<object>lru_key]

        self[key] = value
