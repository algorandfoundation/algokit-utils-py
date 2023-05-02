# Changelog

<!--next-version-placeholder-->

## v1.1.0 (2023-05-02)
### Feature
* Make ensure_funded funding_source parameter optional ([`814661a`](https://github.com/algorandfoundation/algokit-utils-py/commit/814661ae77cb8fcd6ebe7898e134590fe76773d1))
* Add ensure_funded method ([#24](https://github.com/algorandfoundation/algokit-utils-py/issues/24)) ([`e45fc46`](https://github.com/algorandfoundation/algokit-utils-py/commit/e45fc46ed4301ab0f17db1b30e0eae9f4f9ed247))

### Fix
* Handle quoted template variables ([`7cca4f0`](https://github.com/algorandfoundation/algokit-utils-py/commit/7cca4f0d3e62d5c8c797176c515f408699768492))
* Update strip_comments to handle quotes ([`eaa77dd`](https://github.com/algorandfoundation/algokit-utils-py/commit/eaa77dd25c051989d5ba3c120a1e002e2465f432))
* Remove deprecated/renamed functions ([`68f6155`](https://github.com/algorandfoundation/algokit-utils-py/commit/68f6155e439dbd39af665139813e999c53cfceac))
* Correctly adjust port in client configs ([#27](https://github.com/algorandfoundation/algokit-utils-py/issues/27)) ([`89a0848`](https://github.com/algorandfoundation/algokit-utils-py/commit/89a0848f96adda9d3b3b9305799d737ccbc9b304))
* Fix network client auth headers ([#26](https://github.com/algorandfoundation/algokit-utils-py/issues/26)) ([`6ba8792`](https://github.com/algorandfoundation/algokit-utils-py/commit/6ba8792f3652b465ed429d6043428859b52e008b))

### Documentation
* Regenerate docs ([`0cd0717`](https://github.com/algorandfoundation/algokit-utils-py/commit/0cd07171cbe3b906b4d5e4e20a8c61e17cc99761))
* Add link to documentation ([#23](https://github.com/algorandfoundation/algokit-utils-py/issues/23)) ([`2fe6792`](https://github.com/algorandfoundation/algokit-utils-py/commit/2fe6792b565f00c623b5fff98b503525c7e428c7))
* Fix typo in deploy docstring ([#22](https://github.com/algorandfoundation/algokit-utils-py/issues/22)) ([`1229ea4`](https://github.com/algorandfoundation/algokit-utils-py/commit/1229ea4b5194ba980fd194fc4801d81fa8e210e1))

## v1.0.3 (2023-04-18)
### Fix
* Strip comments before compiling to accomodate annotated teal ([#19](https://github.com/algorandfoundation/algokit-utils-py/issues/19)) ([`2bb9a56`](https://github.com/algorandfoundation/algokit-utils-py/commit/2bb9a569036e1847988a7b655d08cd9580fb2608))
* Stop transaction parameters being converted to dict ([#18](https://github.com/algorandfoundation/algokit-utils-py/issues/18)) ([`8e753b5`](https://github.com/algorandfoundation/algokit-utils-py/commit/8e753b5af8af59e7ba901975d300f2b5dc249761))

## v1.0.2 (2023-04-04)
### Fix
* Handle non algosdk TransactionSigner implementations ([#14](https://github.com/algorandfoundation/algokit-utils-py/issues/14)) ([`25be642`](https://github.com/algorandfoundation/algokit-utils-py/commit/25be642466f1b02c3f95c60008670caf9812c3cd))
* Readd AppSpecStateDict type definition to root namespace ([`231e4b8`](https://github.com/algorandfoundation/algokit-utils-py/commit/231e4b880ee154e3edff7425e18ae38cf305a9eb))

### Documentation
* Add .nojekyll ([`f597fbc`](https://github.com/algorandfoundation/algokit-utils-py/commit/f597fbcf86175af6df4d30220338dcee4f0a8b19))
* Publish html version of docs ([#15](https://github.com/algorandfoundation/algokit-utils-py/issues/15)) ([`3e6c0c8`](https://github.com/algorandfoundation/algokit-utils-py/commit/3e6c0c8a44b384e276bd1301d038f2bd867f4727))
* Document all public symbols ([#13](https://github.com/algorandfoundation/algokit-utils-py/issues/13)) ([`954b5e1`](https://github.com/algorandfoundation/algokit-utils-py/commit/954b5e19597ef21ee7f1dcc0e3aa7fca03cb5036))
* Fix typo ([`cb92e08`](https://github.com/algorandfoundation/algokit-utils-py/commit/cb92e08feaa8af6da4ff78356e92674d0d0fe081))

## v1.0.1 (2023-03-29)
### Fix
* Deprecate is_sandbox and get_sandbox_default_account ([#10](https://github.com/algorandfoundation/algokit-utils-py/issues/10)) ([`ad23e57`](https://github.com/algorandfoundation/algokit-utils-py/commit/ad23e57c33fcf692d954f10be8b18b327ae69bd2))
* Rename sandbox to localnet ([`ea43db2`](https://github.com/algorandfoundation/algokit-utils-py/commit/ea43db26000e282364549e739dabdb907468b657))

## v1.0.0 (2023-03-28)
### Breaking
* 1.0 release ([`ef8f280`](https://github.com/algorandfoundation/algokit-utils-py/commit/ef8f28053ce6ac7a03f85b312d249317e3537d3f))

### Documentation
* Add initial documentation for common functionality ([#8](https://github.com/algorandfoundation/algokit-utils-py/issues/8)) ([`ef8f280`](https://github.com/algorandfoundation/algokit-utils-py/commit/ef8f28053ce6ac7a03f85b312d249317e3537d3f))

## v0.2.0 (2023-03-28)
### Feature
* Allow broader types when specifying methods and app_spec in ApplicationClient ([#7](https://github.com/algorandfoundation/algokit-utils-py/issues/7)) ([`b73bb69`](https://github.com/algorandfoundation/algokit-utils-py/commit/b73bb69804a9652fcdb2354f3305e96934d834a4))
* Make ABI call arguments kwargs instead of a dict ([#6](https://github.com/algorandfoundation/algokit-utils-py/issues/6)) ([`574b147`](https://github.com/algorandfoundation/algokit-utils-py/commit/574b14772acce6ae26e05765bf87d1f0dc9d906e))

## v0.1.3 (2023-03-23)
### Fix
* Get_account now works if called a second time for the same account name ([`513dd4c`](https://github.com/algorandfoundation/algokit-utils-py/commit/513dd4c734211fa60d98e5d7b8d01b9aa6b3f830))

## v0.1.2 (2023-03-23)
### Fix
* Expose execute_atc_with_logic_error, allow specifying approval source map ([`f7a887b`](https://github.com/algorandfoundation/algokit-utils-py/commit/f7a887bd688d8527b3559da69bf4426f40fa01d1))
* Resolve sender on __init__ ([`000612d`](https://github.com/algorandfoundation/algokit-utils-py/commit/000612dbfc14f55c0c78341f395710235e562caa))
* Add rekey_to to call method ([#3](https://github.com/algorandfoundation/algokit-utils-py/issues/3)) ([`940e7aa`](https://github.com/algorandfoundation/algokit-utils-py/commit/940e7aaa9794891eb14a120a27c37084e78b4c18))
* Handle app notes with partial data ([#2](https://github.com/algorandfoundation/algokit-utils-py/issues/2)) ([`3cc75db`](https://github.com/algorandfoundation/algokit-utils-py/commit/3cc75db1f40e72da6762c1fe371153a0d610a2b7))

## v0.1.1 (2023-03-22)
### Fix
* Don't mutate provided args when calling ([`c152ed9`](https://github.com/algorandfoundation/algokit-utils-py/commit/c152ed9171d2e734ebae69abb803b60e01e96338))

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
