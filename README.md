perf-scripts
============

Various scripts that give extra battery to linux perf tool

# Requirements

* pandas (any revision should work)

# h5dump

Convert perf.data into a pandas HDFStore file (https://pandas.pydata.org/pandas-docs/stable/reference/io.html#hdfstore-pytables-hdf5)

## Usage

Capture some events with perf

```
 perf record -a -e raw_syscalls:sys_enter
```

Convert perf.data into HDFStore file

```
perf script -s h5dump.py sys_enter.h5
```

## Limitations

* no support for bytearray & list types
