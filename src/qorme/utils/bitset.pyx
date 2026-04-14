cdef extern from "" nogil:
    int __builtin_ctzll(unsigned long long x)
    int __builtin_popcountll(unsigned long long x)


cdef class BitSet:
    cdef unsigned long long value

    def __cinit__(self):
        self.value = 0

    cpdef void set(self, unsigned long long pos):
        self.value |= 1ULL << pos

    cpdef void clear(self, unsigned long long pos):
        self.value &= ~(1ULL << pos)

    cpdef bint has(self, unsigned long long pos):
        return (self.value & (1ULL << pos)) != 0

    cpdef BitSet ior(self, BitSet other):
        self.value |= other.value
        return self

    cpdef object int(self):
        return self.value

    cpdef int length(self):
        return __builtin_popcountll(self.value)

    cpdef list list(self):
        cdef unsigned long long v = self.value
        cdef int pos
        cdef int length = self.length()
        l = [0] * length
        # Iterate only over set bits by removing lowest set bit each time
        for i in range(length):
            # Count trailing zeros to find the index of the least significant set bit
            l[i] = __builtin_ctzll(v)
            # Clear the least significant set bit
            v &= v - 1
        return l
