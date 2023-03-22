# Changelog

<!--next-version-placeholder-->

## v0.1.0 (2023-03-22)
### Feature
* Allow bytes for template_values ([`399bd91`](https://github.com/algorandfoundation/algokit-utils-py/commit/399bd91b863c746c22b8cd75d4539c15c14bc217))
* Make DeleteApp when deploying one transaction across create and delete ([`61f5596`](https://github.com/algorandfoundation/algokit-utils-py/commit/61f5596e7ad4524cdfeb3b8137d50d70ba48de3e))
* Add more details to deploy_app response ([`01aa8a6`](https://github.com/algorandfoundation/algokit-utils-py/commit/01aa8a649f953ef42eaf2c73b29bc5b0df3e0ce8))
* Return ApplicationClient when deploying app ([`dfea9e0`](https://github.com/algorandfoundation/algokit-utils-py/commit/dfea9e0cfe88a7b84300a8dd81c480fd454fdb45))
* Enum for on_update and on_schema_break behaviour ([`3afe65d`](https://github.com/algorandfoundation/algokit-utils-py/commit/3afe65d1b373c81d17660f180d322cf45ccd17a7))
* Add template variables support ([`870ee25`](https://github.com/algorandfoundation/algokit-utils-py/commit/870ee2590c0e8e82ed5a7b2d3792c989d5ce8854))
* Add idempotent deploy ([`685a40f`](https://github.com/algorandfoundation/algokit-utils-py/commit/685a40fddb6e074c28f4d020f218d8ac7dae7924))

### Fix
* Add more typings ([`e8b7371`](https://github.com/algorandfoundation/algokit-utils-py/commit/e8b73717e951e758ef6df525d9b1ce735cb1e33b))
* Always find a clear state bare method ([`8a159b8`](https://github.com/algorandfoundation/algokit-utils-py/commit/8a159b80d45a63dad9450a6881cbdf664fe662c7))
* Pass through additional call parameters ([`3d6ead9`](https://github.com/algorandfoundation/algokit-utils-py/commit/3d6ead9ed83992a3a8174187f095a6e88f0aa71d))
* Allow notes with type str ([`8a8665d`](https://github.com/algorandfoundation/algokit-utils-py/commit/8a8665d686b58392425612877304880d9c824fdb))
* Allow any type for arguments ([`1da1b39`](https://github.com/algorandfoundation/algokit-utils-py/commit/1da1b39bf9ff13cbb3fa08b1ad803371a4ad8c71))
* Fix incorrectly passing schema on bare calls ([`b41f228`](https://github.com/algorandfoundation/algokit-utils-py/commit/b41f228cb4df79845d7b33a8745cc2ea5551f14e))
* ApplicationClient respects None values for allow_update or allow_delete if no deploy-time control being used ([`397981c`](https://github.com/algorandfoundation/algokit-utils-py/commit/397981c82586b0143375221d341ed1dc4446f7e6))
* Define more imports ([`c78ba20`](https://github.com/algorandfoundation/algokit-utils-py/commit/c78ba202e01fb391804c47a4f68a07a169c1a707))
* Define top level imports ([`6c9be52`](https://github.com/algorandfoundation/algokit-utils-py/commit/6c9be52edb348ca1ce345f798ec65d2403e6c746))
* Typing fixes ([`8f9364a`](https://github.com/algorandfoundation/algokit-utils-py/commit/8f9364a061f81f6f5720fdb7c6c9ca7064aca091))
* Review feedback ([`9cceba9`](https://github.com/algorandfoundation/algokit-utils-py/commit/9cceba9e066250657e5ce9809777332a7439a9e0))
* Move wait for indexer function to tests ([`f821df8`](https://github.com/algorandfoundation/algokit-utils-py/commit/f821df8c80d5d042839031a77c1b3e95ebb8f5ed))
* Parse url and replace kmd port more robustly ([`5cba109`](https://github.com/algorandfoundation/algokit-utils-py/commit/5cba1097becec30675771615b22a3489bf50db9c))
* Reduce pyteal dependency, remove global ignores ([`e574133`](https://github.com/algorandfoundation/algokit-utils-py/commit/e5741334418a78b71824fc0ab76d36e0071fdd89))
* Apply changes from review ([`fe52213`](https://github.com/algorandfoundation/algokit-utils-py/commit/fe522135a0f80a8e1d28caa4ac635967eeccc0da))
* Rename DeleteApp to ReplaceApp ([`908a8a6`](https://github.com/algorandfoundation/algokit-utils-py/commit/908a8a63c4260a258f679f20e7bf82a85c709b44))
* Fix ApplicationClient.prepare ([`d1095da`](https://github.com/algorandfoundation/algokit-utils-py/commit/d1095daaf51dff1bab986a1c4f70dbf6ba2b6f93))
* Make app_id and app_address on ApplicationClient readonly ([`6862174`](https://github.com/algorandfoundation/algokit-utils-py/commit/6862174ce93c03461b189b6d9c4727de9366b783))
* Re-add ALGOD_PORT and INDEXER_PORT support ([`82d0218`](https://github.com/algorandfoundation/algokit-utils-py/commit/82d0218ef058bf1da5dfa325dbe8c49a4add9768))
* Ignore apps with no note prefix ([`c82dc60`](https://github.com/algorandfoundation/algokit-utils-py/commit/c82dc60fc7ca6c1a5d02f5cc9ee576b4cc87a9a8))
