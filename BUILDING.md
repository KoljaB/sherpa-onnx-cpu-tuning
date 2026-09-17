# Reproduce the experimental CPU build

This preserves the legacy v1.13.4-cpu.1 build. The current tested configuration
uses official v1.13.8 wheels; see [upgrade and comparison procedure](UPGRADING.md).

Build on Linux x86-64 with CPython 3.12. The published binary was produced on
Ubuntu 24.04 with GCC 13.3.0 and bundled ONNX Runtime 1.27.0. It requires glibc
2.38 and GLIBCXX_3.4.32; this recipe does not claim manylinux portability.

1. Download the sherpa-ONNX v1.13.4 source archive from
   https://github.com/k2-fsa/sherpa-onnx/archive/refs/tags/v1.13.4.tar.gz.
   Verify SHA256 `3243cb386d3a4ac87596adf7d2c89fddf23e2948b154942b987b4d91c1fee295`.
2. Extract into a fresh directory with Python tarfile `filter="data"`, selecting
   regular files and directories only. Some upstream example symlinks are absolute;
   the tested extraction omitted example links. Do not overwrite an existing tree.
3. Run `python tools/prepare_cpu_session_build.py SOURCE_DIR ARTIFACT_DIR` from
   this repository. This validates expected source fragments before writing and
   emits the four-file patch and before/after source hashes.
4. Create a fresh Python 3.12 build venv, and install `build`, `setuptools`, and
   `wheel`. Supply these environment values as one CMake argument string:

```bash
export SHERPA_ONNX_CMAKE_ARGS="-DCMAKE_BUILD_TYPE=Release -DPython_EXECUTABLE=/absolute/path/build-venv/bin/python -DBUILD_SHARED_LIBS=ON -DSHERPA_ONNX_ENABLE_BINARY=OFF -DSHERPA_ONNX_ENABLE_PORTAUDIO=OFF -DSHERPA_ONNX_ENABLE_WEBSOCKET=OFF -DSHERPA_ONNX_BUILD_C_API_EXAMPLES=OFF"
export SHERPA_ONNX_MAKE_ARGS="-j8"
python -m build --no-isolation --wheel --sdist --outdir ARTIFACT_DIR SOURCE_DIR
```

Leave `SHERPA_ONNX_SPLIT_PYTHON_PACKAGE` unset. Use the build venv's Python.
The mixed-case `Python_EXECUTABLE` is required by pybind11's CMake FindPython;
upstream's uppercase `PYTHON_EXECUTABLE` alone selected the wrong Python on the
test host. Verify the wheel tag and native extension both target CPython 3.12.

For source inspection, the release also contains
`sherpa-onnx-cpu1-build-sources.tar.xz`: the already-patched sherpa source tree and
all fetched native dependency source trees from the tested build. Do not apply
the patch generator again to that already-patched tree. Dependency licenses and
copyright notices are preserved. ONNX Runtime was an upstream prebuilt dependency
and is included with its headers, binary and MIT license. A complete source-file
inventory is included as a separate release asset.

CMake's FetchContent dependencies have pinned archives/hashes in upstream's
`cmake/` files. An offline build can point `FETCHCONTENT_SOURCE_DIR_<NAME>` at
the matching dependency directory from the build-sources bundle. The tested
build used upstream's pinned dependency downloads.

Install a resulting wheel into a fresh environment and verify its imports,
model outputs, thread settings, and performance on representative audio before
using it. Preserve the prior environment for rollback. A source rebuild need not
produce a bit-identical wheel, so identify each distributed binary by its SHA256.
