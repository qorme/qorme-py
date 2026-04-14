cimport cython
from cpython.object cimport PyObject
from cpython.pystate cimport PyFrameObject

from qorme.utils.lru_cache cimport LRUCache

import linecache
import os
import sys

import msgspec


cdef extern from "Python.h":
    void Py_INCREF(PyObject*)
    void Py_DECREF(PyObject*)

    ctypedef struct PyCodeObject:
        PyObject *co_filename
        PyObject *co_name

    PyFrameObject *PyEval_GetFrame()
    int PyFrame_GetLineNumber(PyFrameObject*)


cdef extern from "pythoncapi_compat.h":
    PyFrameObject *PyFrame_GetBack(PyFrameObject*)
    PyCodeObject *PyFrame_GetCode(PyFrameObject*)
    PyObject *PyFrame_GetGlobals(PyFrameObject*)


cpdef str get_line(str filename, int lineno):
    cdef list lines = linecache.getlines(filename)
    return lines[lineno - 1] if 0 < lineno <= len(lines) else ""


class TracebackEntry(msgspec.Struct):
    filename: str
    func_name: str
    line: str
    lineno: int


@cython.freelist(512)
cdef class TracebackEntryInfo:
    cdef:
        object data
        bint ignore

    def __cinit__(self, object entry, bint ignore):
        self.data = entry
        self.ignore = ignore


cdef class Traceback:
    cdef:
        int num_entries
        set ignored_modules
        LRUCache file_info_cache, traceback_entries_cache

    def __cinit__(self, object config):
        self.num_entries = config.num_entries
        self.file_info_cache = LRUCache(maxsize=config.file_info_cache_size)
        self.traceback_entries_cache = LRUCache(maxsize=config.entries_cache_size)
        self.ignored_modules = set(
            list(config.default_ignored_modules) + list(config.extra_ignored_modules)
        )

    cpdef list get_stack(self):
        cdef:
            PyFrameObject *frame
            PyFrameObject *last_frame
            PyCodeObject *code
            TracebackEntryInfo entry
            list stack = []
            int i, limit

        if self.num_entries == 0:
            return stack

        if not (last_frame := PyEval_GetFrame()):
            return stack

        Py_INCREF(<PyObject*>last_frame)
        while frame := PyFrame_GetBack(last_frame):
            Py_DECREF(<PyObject*>last_frame)
            last_frame = frame

            code = PyFrame_GetCode(frame)
            entry = self.get_entry(<object>code.co_filename, PyFrame_GetLineNumber(frame), frame, code)
            Py_DECREF(<PyObject*>code)

            if not entry.ignore:
                stack.append(entry.data)
                break

        limit = self.num_entries - 1
        for i in range(limit):
            if not (frame := PyFrame_GetBack(last_frame)):
                break
            Py_DECREF(<PyObject*>last_frame)
            last_frame = frame

            code = PyFrame_GetCode(frame)
            entry = self.get_entry(<object>code.co_filename, PyFrame_GetLineNumber(frame), frame, code)
            Py_DECREF(<PyObject*>code)
            stack.append(entry.data)

        Py_DECREF(<PyObject*>last_frame)
        return stack

    cdef TracebackEntryInfo get_entry(self, str filename, int lineno, PyFrameObject *frame, PyCodeObject *code):
        cache_key = filename, lineno
        if (ret := self.traceback_entries_cache.get(cache_key)) is None:
            rel_path, ignore = self.get_file_info(filename, frame)
            data = TracebackEntry(rel_path, <object>code.co_name, get_line(filename, lineno), lineno)
            ret = TracebackEntryInfo(data, ignore)
            self.traceback_entries_cache.set(cache_key, ret)
        return ret

    cdef tuple get_file_info(self, str filename, PyFrameObject *frame):
        cdef str rel_path, module_dir

        if (info := self.file_info_cache.get(filename)) is not None:
            return info

        # Get module name from frame globals
        f_globals = PyFrame_GetGlobals(frame)
        module = (<dict>f_globals).get("__name__", "")
        Py_DECREF(f_globals)

        # Find the root module and its directory
        module_dir = None
        root_module_name = module.split(".", 1)[0] if module else ""
        if root_module := sys.modules.get(root_module_name):
            # Try to get module directory from __file__ or __path__
            try:
                if getattr(root_module, "__file__", None):
                    # Go up 2 levels: pkg/__init__.py -> pkg -> parent
                    module_dir = root_module.__file__.rsplit(os.sep, 2)[0]
                elif getattr(root_module, "__path__", None) and isinstance(root_module.__path__, (list, tuple)):
                    # Namespace package: use first path entry
                    module_dir = root_module.__path__[0].rsplit(os.sep, 1)[0]
            except Exception:
                pass

            if module_dir:
                # Simple string split to get relative path (Scout APM's approach)
                rel_path = filename.split(module_dir, 1)[-1].lstrip(os.sep)
            else:
                rel_path = os.path.basename(filename)
        else:
            # No module info - just use basename
            rel_path = os.path.basename(filename)

        ignore = any(m in filename for m in self.ignored_modules)
        file_info = rel_path, ignore
        self.file_info_cache.set(filename, file_info)
        return file_info
