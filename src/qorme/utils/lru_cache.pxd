cdef class LRUCache(dict):
    cdef readonly int maxsize

    cpdef get(self, key)
    cpdef void set(self, key, value)
