# CHANGELOG



## v1.4.0 (2024-04-19)

### Feature

* feat: conda self hosted uploads and fix deprecation warnings (#30) ([`f41bc9c`](https://github.com/AibelDevs/action-toolbox/commit/f41bc9c52d82627d760e40485d8e2df128035272))


## v1.3.4 (2023-12-21)

### Fix

* fix: docker / gitops inputs and docker latest tag to action_config.yaml (#23)

Co-authored-by: Vegar Ringdal &lt;vegar.ringdal@gmail.com&gt;
Co-authored-by: krande &lt;kristoffer_andersen@outlook.com&gt; ([`d57c035`](https://github.com/AibelDevs/action-toolbox/commit/d57c0356dcce5933f1aa719c58141dc8a8be3a97))


## v1.3.3 (2023-12-20)

### Fix

* fix: catch yaml issues in gitops (#22) ([`46f9ad3`](https://github.com/AibelDevs/action-toolbox/commit/46f9ad33c87ab9b9ea07bb7e8ea5ef95f783effd))


## v1.3.2 (2023-12-20)

### Fix

* fix: use graceful exit for pr version calc (#21) ([`b482654`](https://github.com/AibelDevs/action-toolbox/commit/b4826542290b58c52ae1f37f4a5d1af7e6dc1c65))


## v1.3.1 (2023-12-18)

### Fix

* fix: Manual dispatch (#19) ([`6ecded3`](https://github.com/AibelDevs/action-toolbox/commit/6ecded3dfe29e3b7d5585468af762e45c4babcd0))

* fix: calculate version / release when using skip release (#18)

Co-authored-by: Vegar Ringdal &lt;vegar.ringdal@gmail.com&gt;
Co-authored-by: krande &lt;kristoffer_andersen@outlook.com&gt; ([`e4a5034`](https://github.com/AibelDevs/action-toolbox/commit/e4a5034ad32dad6aa5209e1b330f30c130f22a27))

### Unknown

* update tool for pr version calculate and add a manual dispatch example ([`0067f95`](https://github.com/AibelDevs/action-toolbox/commit/0067f95a7334fef6d911a42893a76cca4572d1d8))


## v1.3.0 (2023-12-15)

### Feature

* feat: allow passing in the desired pre-release level for dispatch workflows (#16) ([`ed9e3d1`](https://github.com/AibelDevs/action-toolbox/commit/ed9e3d178aff091b41e35682ee94ede1a47fe855))


## v1.2.3 (2023-12-15)

### Fix

* fix: do not test conda package during publish task (#15) ([`735fb31`](https://github.com/AibelDevs/action-toolbox/commit/735fb31a16231d22babd653e35fc8eb946c4341b))


## v1.2.2 (2023-12-15)

### Fix

* fix: add fix for pre-release number calculation on repositories with other… (#14) ([`525936a`](https://github.com/AibelDevs/action-toolbox/commit/525936a6a9bfdead89ffca9c33992720048a604e))


## v1.2.1 (2023-12-14)

### Fix

* fix: add missing json module and have the option of testing silence-bot label (#13) ([`4c67fc0`](https://github.com/AibelDevs/action-toolbox/commit/4c67fc0c6031fe6acf054a02267e5922ac9f8d92))


## v1.2.0 (2023-12-14)

### Feature

* feat: add option for adding extra conda channel (#12) ([`0c6ea6e`](https://github.com/AibelDevs/action-toolbox/commit/0c6ea6e60b7c39e46d8f49606662c40948b95de8))


## v1.1.1 (2023-12-13)

### Fix

* fix: Fix bug in pylint linting and issues from previous workflow split (#11) ([`1eb661e`](https://github.com/AibelDevs/action-toolbox/commit/1eb661e4338a3aed2fde093240687d5602850d44))


## v1.1.0 (2023-12-13)

### Feature

* feat: Add simplified default tools and fix pre-release bumping py and json projects (#10) ([`fe699a8`](https://github.com/AibelDevs/action-toolbox/commit/fe699a8171999e940ef8c58c02f072a9ab6f7e2b))


## v1.0.0 (2023-12-12)

### Breaking

* feat!: initial stable release (#7) ([`4d7e254`](https://github.com/AibelDevs/action-toolbox/commit/4d7e254fc3486d86909a04bb11676eb5ea4b5b09))

### Chore

* chore: add code for forcing releases ([`34c13fa`](https://github.com/AibelDevs/action-toolbox/commit/34c13faa937f11877d55cbb144324f3d1a695e42))

* chore: try using pr head ([`a948b7e`](https://github.com/AibelDevs/action-toolbox/commit/a948b7e8bca954018a1208b859b7c99e11ce26fa))

* chore: expand fetch depth ([`2a0f6b2`](https://github.com/AibelDevs/action-toolbox/commit/2a0f6b2c027a4672ac8732f3bef693289bdfc4a1))

* chore: print errors also ([`7d9f196`](https://github.com/AibelDevs/action-toolbox/commit/7d9f19684adc6bf8c42d28f239c3b379321e4cda))

* chore: Add missing inputs to workflows and minor conda fixes (#6) ([`d0673bc`](https://github.com/AibelDevs/action-toolbox/commit/d0673bcdcda6d38340567a2997900413e918b779))

* chore: add missing json module import (#5) ([`4ddb80a`](https://github.com/AibelDevs/action-toolbox/commit/4ddb80a4be56ec9e40aaf0a229381414afbee70e))

* chore: add calculation preview of next version (#4) ([`5e07665`](https://github.com/AibelDevs/action-toolbox/commit/5e0766547402f256d6d8a10530b70601b71a4592))

### Unknown

* remove unused step ([`dbf846a`](https://github.com/AibelDevs/action-toolbox/commit/dbf846a6b06a9f0fda712732f4f4da1960516d2c))

* minor change ([`f535273`](https://github.com/AibelDevs/action-toolbox/commit/f53527323973417d5c9f9d0ba934109b46d4434f))


## v0.0.1 (2023-12-12)

### Fix

* fix: minor change (#3) ([`6fe799f`](https://github.com/AibelDevs/action-toolbox/commit/6fe799f7fce1e1da9b01c10e47342eb403f04528))

* fix: minor change in readme (#1) ([`c711833`](https://github.com/AibelDevs/action-toolbox/commit/c71183317af72404b63cf83bc36acb7da27c33eb))

### Unknown

* update action_config.toml (#2) ([`cd05bf6`](https://github.com/AibelDevs/action-toolbox/commit/cd05bf6a853618509b0093ff564ae88491a33e74))

* improve readme ([`db8fe7c`](https://github.com/AibelDevs/action-toolbox/commit/db8fe7c7f6766d2ecf613100df9e11d60d88a344))

* add PR review and tag sample and config toml ([`cd04828`](https://github.com/AibelDevs/action-toolbox/commit/cd04828a0a638bdd55b7991c31322133faa139fd))

* remove todo&#39;s ([`594e7c6`](https://github.com/AibelDevs/action-toolbox/commit/594e7c62eed7aa1d6e229ec896a2d1ad201c1b45))

* initial commit ([`e771258`](https://github.com/AibelDevs/action-toolbox/commit/e771258fc5fb271b1bb2360b573260a6143e2711))
