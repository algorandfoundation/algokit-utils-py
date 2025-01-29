# AlgoKit Python Utilities

A set of core Algorand utilities written in Python and released via PyPi that make it easier to build solutions on Algorand.
This project is part of [AlgoKit](https://github.com/algorandfoundation/algokit-cli).

The goal of this library is to provide intuitive, productive utility functions that make it easier, quicker and safer to build applications on Algorand.
Largely these functions wrap the underlying Algorand SDK, but provide a higher level interface with sensible defaults and capabilities for common tasks.

> **Note**
> If you prefer TypeScript there's an equivalent [TypeScript utility library](https://github.com/algorandfoundation/algokit-utils-ts).

[Install](https://github.com/algorandfoundation/algokit-utils-py#install) | [Documentation](https://algorandfoundation.github.io/algokit-utils-py/html/index.html)

## Install

This library can be installed using pip, e.g.:

```
pip install algokit-utils
```

## Migration from `v2.x` to `v3.x`

Refer to the [v3 migration guide](./docs/source/v3-migration-guide.md) for more information on how to migrate to latest version of `algokit-utils-py`.

## Guiding principles

This library follows the [Guiding Principles of AlgoKit](https://github.com/algorandfoundation/algokit-cli/blob/main/docs/algokit.md#guiding-principles).

## Contributing

This is an open source project managed by the Algorand Foundation.
See the [AlgoKit contributing page](https://github.com/algorandfoundation/algokit-cli/blob/main/CONTRIBUTING.MD) to learn about making improvements.

To successfully run the tests in this repository you need to be running LocalNet via [AlgoKit](https://github.com/algorandfoundation/algokit-cli):

```
algokit localnet start
```
