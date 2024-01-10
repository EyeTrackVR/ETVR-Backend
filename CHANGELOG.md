# 📦 Changelog 
[![conventional commits](https://img.shields.io/badge/conventional%20commits-1.0.0-yellow.svg)](https://conventionalcommits.org)
[![semantic versioning](https://img.shields.io/badge/semantic%20versioning-2.0.0-green.svg)](https://semver.org)
> All notable changes to this project will be documented in this file

## [1.6.0](https://github.com/EyeTrackVR/ETVR-Backend/compare/v1.5.0...v1.6.0) (2024-01-10)


### 🍕 Features

* added default index page ([b5ce133](https://github.com/EyeTrackVR/ETVR-Backend/commit/b5ce133d9d64ced0c020752e4b9072bf8bd7720f))
* added delta time to process class ([df2886a](https://github.com/EyeTrackVR/ETVR-Backend/commit/df2886a96de89e6a95be5d9c4feaa9fe78399e92))
* added frame number and fps to serial cams ([2568118](https://github.com/EyeTrackVR/ETVR-Backend/commit/2568118915810be642e2f031661038d978827719))
* added optional process afifnity masking ([ab6f8f0](https://github.com/EyeTrackVR/ETVR-Backend/commit/ab6f8f08e0373d8add78e147feef150396cc3f90))
* implemented camera streams for frontend ([3ec2772](https://github.com/EyeTrackVR/ETVR-Backend/commit/3ec2772e64443808811cdd15e07360952ce2d1f7))
* implemented frame rotation again ([7617abe](https://github.com/EyeTrackVR/ETVR-Backend/commit/7617abe8746c49d9b67a6aa77caab9db3408479a))
* implemented serial camera support ([7adcbd6](https://github.com/EyeTrackVR/ETVR-Backend/commit/7adcbd683d38306b0ceaed919f5f0326ad20de98))
* Linux support for serial cameras ([f702c59](https://github.com/EyeTrackVR/ETVR-Backend/commit/f702c59257501b53cf693ce4c301d989751d3ebf))


### 🐛 Bug Fixes

* asset subfolders are now included in builds ([d61c84d](https://github.com/EyeTrackVR/ETVR-Backend/commit/d61c84dc89b898d0b1636e1b87bbb3896e75047d))
* dont pass duplicate config to OSC ([31a819f](https://github.com/EyeTrackVR/ETVR-Backend/commit/31a819faae071203a549076bc43fbadeca7d0b1d))
* fix visualizer memory leak ([3c67478](https://github.com/EyeTrackVR/ETVR-Backend/commit/3c6747810c05691c46bc2cd7c4fe0884142c80c7))
* fixed bug where config wasnt monitored ([0f475fc](https://github.com/EyeTrackVR/ETVR-Backend/commit/0f475fcc569ad432ebd0b976b138579f6f052f6d))
* fixed config json string encoding ([832e4a5](https://github.com/EyeTrackVR/ETVR-Backend/commit/832e4a5a3a8bf619ffb2674374b5b41a69b355ea))
* fixed delta time being 0 on rare occasions ([7562c79](https://github.com/EyeTrackVR/ETVR-Backend/commit/7562c7950602b3346ae2316b14f41774baf7d14f))
* fixed incorrect perspective on left eye ([8c8ce5e](https://github.com/EyeTrackVR/ETVR-Backend/commit/8c8ce5e4e795649b2ab456d7eaa076f76ad90208))
* fixed leap visualization with ROI cropping ([408afdd](https://github.com/EyeTrackVR/ETVR-Backend/commit/408afdd0c5e724cb517b0a8f4672ab73b4f77b9d))
* fixed OpenCV dumbness ([53a3a36](https://github.com/EyeTrackVR/ETVR-Backend/commit/53a3a361a266c6d7394ac703c6a09c1b29d45365))
* fixed OSC receiver port collisions ([7366ede](https://github.com/EyeTrackVR/ETVR-Backend/commit/7366edebd01e234a9af31123da361604e956c874))
* Fixed OSC receiver thread not being created ([5b768cf](https://github.com/EyeTrackVR/ETVR-Backend/commit/5b768cfb72ceb9f9560f7651c8ecae8fa003bbdd))
* fixed process config mismatches ([18cb6b1](https://github.com/EyeTrackVR/ETVR-Backend/commit/18cb6b1e19000cfd4c89a9d1fb01e8a85870d67e))
* fixed streams not closing when trackers stop ([871024c](https://github.com/EyeTrackVR/ETVR-Backend/commit/871024c3e36bf8569266461189743a0cb79113da))
* fixed validation correction not being saved ([c7c3daa](https://github.com/EyeTrackVR/ETVR-Backend/commit/c7c3daadc25eb9b23457bb9ac2d210efc1d53e31))
* fixed visualizer blocking the event loop ([a835b3b](https://github.com/EyeTrackVR/ETVR-Backend/commit/a835b3bfbfbbb185dfad4d5942533ebb9ac1ee07))
* move `pytest-asyncio` to dev dependencies ([71b2e27](https://github.com/EyeTrackVR/ETVR-Backend/commit/71b2e27e6b98fba223865ea7b6f8bd7ccf3ec326))
* Queues are cleared if there is backpressure ([cb19c43](https://github.com/EyeTrackVR/ETVR-Backend/commit/cb19c43a8906208e9f81d37d24b4be117fa2b40c))
* removed unused debug code ([0ed63e0](https://github.com/EyeTrackVR/ETVR-Backend/commit/0ed63e06bf1c74cd3b46e9e37ca0d05509ccc1cc))
* thread shutdown error with pyinstaller ([b5075f3](https://github.com/EyeTrackVR/ETVR-Backend/commit/b5075f3647885b848c8ebe546e5c4395662dc4d6))
* y axis flipping ([66c50bb](https://github.com/EyeTrackVR/ETVR-Backend/commit/66c50bbaca78905b263dd7950f8513d107d53eaa))


### 📝 Documentation

* added a bunch of info to the README ([57392b6](https://github.com/EyeTrackVR/ETVR-Backend/commit/57392b64e057e035bfd21e54f1158555045477f4))


### 🧑‍💻 Code Refactoring

* abstracted and simplified config code ([2c2f2a4](https://github.com/EyeTrackVR/ETVR-Backend/commit/2c2f2a4503ed69b50188d2a5354bc1e2af1bf28d))
* added image utils ([a6a02b7](https://github.com/EyeTrackVR/ETVR-Backend/commit/a6a02b77f2f612675e961019732bb1b5f39869f8))
* mark all constants as `Final` ([7d61c65](https://github.com/EyeTrackVR/ETVR-Backend/commit/7d61c65085cfa68a641810ab90f8a646fd6a5f5a))
* redid asset folder structure ([056bd59](https://github.com/EyeTrackVR/ETVR-Backend/commit/056bd590496625cfa3992a47d2641ecbbfbab4de))
* update tests to work with new config ([f884c3b](https://github.com/EyeTrackVR/ETVR-Backend/commit/f884c3b1d47e777ff153e2b2b2f9f2b194969c7e))


### 🤖 Build System

* added `pyserial` ([f5bdb6c](https://github.com/EyeTrackVR/ETVR-Backend/commit/f5bdb6c35cf4e37bd90869364b2889489069a589))
* added psutil ([f270cc0](https://github.com/EyeTrackVR/ETVR-Backend/commit/f270cc0bf73b015bac4feab97a3403e5d33c979a))
* dont run CI/CD twice on pull requests ([c3b32ce](https://github.com/EyeTrackVR/ETVR-Backend/commit/c3b32ce432b72a269a4480d1860a0a330cae98e0))
* **fix:** fixed CI/CD tag ignores ([9301182](https://github.com/EyeTrackVR/ETVR-Backend/commit/93011820ef96a3f08298eeb2d4da5165910056c4))
* ignore release candidates ([9e2aab9](https://github.com/EyeTrackVR/ETVR-Backend/commit/9e2aab9dc5af2a17e56b60f1633f2ca55b0035ba))
* remove unused dependencies ([b417734](https://github.com/EyeTrackVR/ETVR-Backend/commit/b4177340d08f1da9a503efcdb3347fd993db9033))
* Updated ruff to latest version ([1e24e5a](https://github.com/EyeTrackVR/ETVR-Backend/commit/1e24e5a0586845c09035a7da3de891e2768f8c58))

## [1.5.0](https://github.com/EyeTrackVR/ETVR-Backend/compare/v1.4.1...v1.5.0) (2023-11-07)


### 🍕 Features

* **patch:** added ROI cropping ([05bfbff](https://github.com/EyeTrackVR/ETVR-Backend/commit/05bfbff845e8dae0df760361b3175cf375f34215))

## [1.4.1](https://github.com/EyeTrackVR/ETVR-Backend/compare/v1.4.0...v1.4.1) (2023-10-17)


### 🐛 Bug Fixes

* fixed new config not being created ([3c45783](https://github.com/EyeTrackVR/ETVR-Backend/commit/3c45783519711c96faea74733b98fc81a327243a))

## [1.4.0](https://github.com/EyeTrackVR/ETVR-Backend/compare/v1.3.1...v1.4.0) (2023-10-17)


### 🍕 Features

* added debug flag ([d2c04da](https://github.com/EyeTrackVR/ETVR-Backend/commit/d2c04dae43e7712544afa7be2a98b7f3547dcb6f))
* apply `OneEuroFilter` before sending OSC ([021c268](https://github.com/EyeTrackVR/ETVR-Backend/commit/021c268957e7aba01ade4d676f431964ab775c3e))
* hide all debug visuals behind config `debug` ([0c51ba7](https://github.com/EyeTrackVR/ETVR-Backend/commit/0c51ba731dfc0cf24b2667dd4b2f80ee33c64115))
* Updated to python 3.11 ([a21c334](https://github.com/EyeTrackVR/ETVR-Backend/commit/a21c334f5bf4d6deada92364d32af10e5b0b48da))


### 🐛 Bug Fixes

* fixed `cv2.Mat` type hints ([37e4cf6](https://github.com/EyeTrackVR/ETVR-Backend/commit/37e4cf6d7fb1340e21f9f2706c9bc540834661e0))
* fixed config saving itself infinitely ([13e57ff](https://github.com/EyeTrackVR/ETVR-Backend/commit/13e57ffcf7763fb4122258896f64e042b34045db))
* fixed divide by 0 error in one euro filter ([5a01fe1](https://github.com/EyeTrackVR/ETVR-Backend/commit/5a01fe12c4ad8e3790c8508885c9bf110494f5d1))
* fixed rare bug where the config was always corrupt ([694bb41](https://github.com/EyeTrackVR/ETVR-Backend/commit/694bb413f9fbbdd991243a7d56f9f8fc37b074c2))
* fixed some type errors ([42a54c7](https://github.com/EyeTrackVR/ETVR-Backend/commit/42a54c77c031617e682e8cbeba5d679d8374e6cd))
* fixed trackers using old config after updates ([26064f5](https://github.com/EyeTrackVR/ETVR-Backend/commit/26064f50eeb0d66e0607c7347b91f12e564a6729))
* master config now reacts to file updates ([63558d1](https://github.com/EyeTrackVR/ETVR-Backend/commit/63558d1b137bcc8db5ae7862770644ee428637d5))
* pydantic validation error ([6677a60](https://github.com/EyeTrackVR/ETVR-Backend/commit/6677a602d31efb8278d1e2495f80f3cff5b883d1))
* upped maximum frame backlog ([97d4516](https://github.com/EyeTrackVR/ETVR-Backend/commit/97d451661e0fcd32f392ef256cd4d55f20dbaed0))


### 🧑‍💻 Code Refactoring

* abstracted config watcher into a class ([06e63cf](https://github.com/EyeTrackVR/ETVR-Backend/commit/06e63cfc158f161e53e5683108940763d1ba1d7c))
* give each tracker its own OSC sender ([c76c8d3](https://github.com/EyeTrackVR/ETVR-Backend/commit/c76c8d31da7b513fbce0ec20bed110770790a5bf))
* moved `OneEuroFilter` to its own file ([daab001](https://github.com/EyeTrackVR/ETVR-Backend/commit/daab001d82956dcac96beaf032c9089ce6b029cd))
* redid how debug flags are handled ([81f82bb](https://github.com/EyeTrackVR/ETVR-Backend/commit/81f82bb63589048e82d14ee9a62e15afeb964175))
* use `Self` return type ([0393bb6](https://github.com/EyeTrackVR/ETVR-Backend/commit/0393bb681be1966493d8edac79e5a6c680a918db))
* use built in `StrEnum` ([9f0e5c9](https://github.com/EyeTrackVR/ETVR-Backend/commit/9f0e5c9d8f951f4860017ebbd58a4e12588109f1))


### 🤖 Build System

* Update python version ([a62d5dc](https://github.com/EyeTrackVR/ETVR-Backend/commit/a62d5dc4113dfaa0e735380078edd6b612f66242))
* Upgrade ruff ([af8f74d](https://github.com/EyeTrackVR/ETVR-Backend/commit/af8f74d4c4f1c8cf527f9a366d686ef483e8763d))

## [1.3.1](https://github.com/EyeTrackVR/ETVR-Backend/compare/v1.3.0...v1.3.1) (2023-10-10)


### 🔥 Performance Improvements

* general optimizations ([8f64470](https://github.com/EyeTrackVR/ETVR-Backend/commit/8f64470b291e842042198776eb3038d82fea6e95))

## [1.3.0](https://github.com/EyeTrackVR/ETVR-Backend/compare/v1.2.2...v1.3.0) (2023-10-09)


### 🍕 Features

* Added leap ([e65d1e4](https://github.com/EyeTrackVR/ETVR-Backend/commit/e65d1e4dfb2660294d0aa3dd00e20ab74eb7c2e3))
* Added OneEuroFilter ([000574b](https://github.com/EyeTrackVR/ETVR-Backend/commit/000574b394abc997be6c8f8cdc6209cf68a015ea))


### 🐛 Bug Fixes

* moved normalization to the OSC process ([69e2f2a](https://github.com/EyeTrackVR/ETVR-Backend/commit/69e2f2a7b956e2b7cabc8aecfc9bbefd12220f20))


### 🤖 Build System

* added onnxruntime ([b42ae07](https://github.com/EyeTrackVR/ETVR-Backend/commit/b42ae07ea46d63f511555453b774fa317b7a099a))

## [1.2.2](https://github.com/EyeTrackVR/ETVR-Backend/compare/v1.2.1...v1.2.2) (2023-10-08)


### 🐛 Bug Fixes

* general optimizations / cleanup ([3675301](https://github.com/EyeTrackVR/ETVR-Backend/commit/36753018409d5a7b4e46ddc189f1ec0c85913f35))

## [1.2.1](https://github.com/EyeTrackVR/ETVR-Backend/compare/v1.2.0...v1.2.1) (2023-10-06)


### 🤖 Build System

* added general use build script ([ffa2aa3](https://github.com/EyeTrackVR/ETVR-Backend/commit/ffa2aa34ad2fc0066319be40ccf1d96f1b569837))

## [1.2.0](https://github.com/EyeTrackVR/ETVR-Backend/compare/v1.1.0...v1.2.0) (2023-09-23)


### 🍕 Features

* Added endpoint to reset config/trackers ([020b291](https://github.com/EyeTrackVR/ETVR-Backend/commit/020b291e5f83a3c4d97e8f8f3aa41897e88eec92))

## [1.1.0](https://github.com/EyeTrackVR/ETVR-Backend/compare/v1.0.4...v1.1.0) (2023-09-18)


### 🍕 Features

* added __repr__ to processor class ([6c6028e](https://github.com/EyeTrackVR/ETVR-Backend/commit/6c6028ea1cf2cfeac7edf53bd6604c66d23fc6f9))
* added device config class ([0c3cca8](https://github.com/EyeTrackVR/ETVR-Backend/commit/0c3cca894e131ee74ded26ec1d514ee7d7a59bf9))
* added method to get tracker by uuid ([cbc1e25](https://github.com/EyeTrackVR/ETVR-Backend/commit/cbc1e259d0736c35e7a75ed167d6cf9ed305a939))
* added new endpoints to manage trackers ([5023f32](https://github.com/EyeTrackVR/ETVR-Backend/commit/5023f32319394bcffeef355bb9b9ab598a35057b))
* added support for dynamic trackers ([60b0b02](https://github.com/EyeTrackVR/ETVR-Backend/commit/60b0b02ad920bddd32d78d845a342c7e9b941ee1))
* added tracker config update callback ([8d38031](https://github.com/EyeTrackVR/ETVR-Backend/commit/8d3803106a9bc4966e5477d3d9861908e3aa0905))


### 🐛 Bug Fixes

* fixed generating configs when bundled ([428c422](https://github.com/EyeTrackVR/ETVR-Backend/commit/428c42276d41d7bfc6207be56035fa9fae8c8ba7))
* newer backup configs replace older ones ([ba58882](https://github.com/EyeTrackVR/ETVR-Backend/commit/ba588820fabb10f41760f7b520cf7a26d954fafa))
* return newly created tracker config ([5d3cd33](https://github.com/EyeTrackVR/ETVR-Backend/commit/5d3cd33b51621798bed80b8e121675db8b936938))


### 📝 Documentation

* added documentation for FastAPI ([666ef3c](https://github.com/EyeTrackVR/ETVR-Backend/commit/666ef3c127551ca55da63fdb229a2af4ab3d1909))


### 🧑‍💻 Code Refactoring

* rename device to tracker ([31cd1f7](https://github.com/EyeTrackVR/ETVR-Backend/commit/31cd1f7da14a3c12e404194985d7e72f49a042d1))

## [1.0.4](https://github.com/EyeTrackVR/ETVR-Backend/compare/v1.0.3...v1.0.4) (2023-09-07)


### 🤖 Build System

* enabled `pyproject.toml` versioning ([33f3908](https://github.com/EyeTrackVR/ETVR-Backend/commit/33f390835a9ad1ef4da245ce7a35946cb88cc285))

## [1.0.3](https://github.com/EyeTrackVR/ETVR-Backend/compare/v1.0.2...v1.0.3) (2023-09-07)


### 🐛 Bug Fixes

* fixed model validation for config updates ([987e65f](https://github.com/EyeTrackVR/ETVR-Backend/commit/987e65fa3a34cfb8d2cbc3de0f73eabe44f75d50))


### 📝 Documentation

* add virtual environment instructions ([fb3eaba](https://github.com/EyeTrackVR/ETVR-Backend/commit/fb3eaba19b012f201f3a74d289a33dd99678f7a9))


### 🤖 Build System

* Update build.yml to fix early-exit bug ([b46d299](https://github.com/EyeTrackVR/ETVR-Backend/commit/b46d2998a65a41b76c0f65f883f06b4a8877bf2e))

## [1.0.2](https://github.com/ShyAssassin/ETVR-Backend/compare/v1.0.1...v1.0.2) (2023-07-31)


### 🐛 Bug Fixes

* custom config paths work now ([b0e5b1d](https://github.com/ShyAssassin/ETVR-Backend/commit/b0e5b1dde9b3fcad2fb9b8736f2796c8910050ec))

## [1.0.1](https://github.com/ShyAssassin/ETVR-Backend/compare/v1.0.0...v1.0.1) (2023-07-30)


### 🤖 Build System

* Update prepareCMD.sh ([a2bc6e7](https://github.com/ShyAssassin/ETVR-Backend/commit/a2bc6e7ad97f86684becf8768ff8e0f9ef8c050b))

## 1.0.0 (2023-07-30)


### 🍕 Features

* add docker system for each development ([83f3c70](https://github.com/ShyAssassin/ETVR-Backend/commit/83f3c70f903abe7c509073f7a3b889c814105cb6))
* add mdns.py ([2c5723a](https://github.com/ShyAssassin/ETVR-Backend/commit/2c5723a0e63e2a6d7d7cb5a8596814660cd2ab59))
* add thunder client ([637434b](https://github.com/ShyAssassin/ETVR-Backend/commit/637434bfdadd322e2061143787c96f735ad31926))
* setting up automation ([f72aa60](https://github.com/ShyAssassin/ETVR-Backend/commit/f72aa607bbe9d34e9ab19ed1cc4641cd3f8a6760))
* setting up automation ([f55dd43](https://github.com/ShyAssassin/ETVR-Backend/commit/f55dd436bc92c1731ccf7099752d378d8feeea49))


### 🐛 Bug Fixes

* dev container now runs correctly ([2323964](https://github.com/ShyAssassin/ETVR-Backend/commit/2323964f05b8ca53c7d0d4b5e744c3a5317a9672))
* docker container failing to build ([9d27b94](https://github.com/ShyAssassin/ETVR-Backend/commit/9d27b94bccbafe958f66805f46d45e313eca875e))
* docker img to 3.11 ([fd63abb](https://github.com/ShyAssassin/ETVR-Backend/commit/fd63abb09097fe4e0884bff248edf49ad528d45d))
* issue with install command ([2302f7f](https://github.com/ShyAssassin/ETVR-Backend/commit/2302f7f18698c0cfc35a4989cbc1aec410c10199))
* remove websocket handle ([23396bd](https://github.com/ShyAssassin/ETVR-Backend/commit/23396bd2a68cffb4f4853bdedf77676d09ed4ebf))
* update readme ([b498ef0](https://github.com/ShyAssassin/ETVR-Backend/commit/b498ef096956408267ea87747d0f802106a0d286))


### 🧑‍💻 Code Refactoring

*  update README ([a71619a](https://github.com/ShyAssassin/ETVR-Backend/commit/a71619a11a27adb9899e98f78ae9b10c935bcc8d))

## [1.0.4](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/compare/v1.0.3...v1.0.4) (2023-07-30)


### 🔁 Continuous Integration

* **ci-fix:** migrate to one-file install ([eb4b2d7](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/eb4b2d7024877b3ca67830d109f17148da61690b))
* **ci-fix:** migrate to one-file install ([588bd59](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/588bd596fcc8d448156dfce21388965d67c4ce7e))

## [1.0.3](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/compare/v1.0.2...v1.0.3) (2023-07-30)


### 🔁 Continuous Integration

* **ci-fix:** migrate to one-file install ([aecc796](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/aecc796dde33e02c68b99c309cd08edb036f46e2))

## [1.0.2](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/compare/v1.0.1...v1.0.2) (2023-07-30)


### 🔁 Continuous Integration

* **ci-fix:** migrate to one-file install ([c7b4f1b](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/c7b4f1b9bf35fdc77a4081732e94a924b623fa72))
* **ci-fix:** migrate to one-file install ([49de7fe](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/49de7fefc091b097d077217cbd4a4634c3431628))
* **ci-fix:** migrate to one-file install ([cd6e2fe](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/cd6e2fe8d44115222ee85f7da89485659dbfcdde))
* **ci-fix:** migrate to one-file install ([0f230fb](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/0f230fb69abf8daf38553b9342cc79bb469e29c7))
* **ci-fix:** migrate to one-file install ([a9600d3](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/a9600d3590e1188034d55668c3b639282469da7c))

## [1.0.1](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/compare/v1.0.0...v1.0.1) (2023-07-30)


### 🔁 Continuous Integration

* **ci-fix:** fix semantic-release dependancy ([fcd957a](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/fcd957a1f9be95606fbabe7d2d5c062947a0445a))
* **ci-fix:** migrate to manual build ([147336b](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/147336b7016f141a686f6ef9a1b56e24fc0fe595))
* **ci-fix:** migrate to manual build ([1835632](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/18356321e017f0b67cc81ca7d9d2af8114df5316))
* **ci-fix:** migrate to manual build ([db020a1](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/db020a1102ad056f28df31641852d2786fa4c135))
* **ci-fix:** migrate to manual build ([db1a998](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/db1a99884c893476787117cb0834a75cf2e71f5e))
* **ci-fix:** migrate to manual build ([d257edb](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/d257edb6f9e12baf92bd21c6c5e126f2f07f6a61))
* **ci-fix:** setup linux deps ([75befed](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/75befed81d46bac1148e14114299190688961385))
* **ci-fix:** setup windows build requirements ([19e75c5](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/19e75c515fa44e3efe4e3a501520524f2cda021c))
* **ci-fix:** setup windows build requirements ([e4fa6d1](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/e4fa6d18adb7377329010510906e0a0e4d571a58))
* **ci-fix:** setup windows build requirements ([5af4fed](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/5af4fed415727487d85180b79cb8a03d98c14edc))

## 1.0.0 (2023-07-30)


### 🍕 Features

* add docker system for each development ([83f3c70](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/83f3c70f903abe7c509073f7a3b889c814105cb6))
* add mdns.py ([2c5723a](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/2c5723a0e63e2a6d7d7cb5a8596814660cd2ab59))
* add thunder client ([637434b](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/637434bfdadd322e2061143787c96f735ad31926))
* setting up automation ([f72aa60](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/f72aa607bbe9d34e9ab19ed1cc4641cd3f8a6760))
* setting up automation ([f55dd43](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/f55dd436bc92c1731ccf7099752d378d8feeea49))


### 🐛 Bug Fixes

* dev container now runs correctly ([2323964](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/2323964f05b8ca53c7d0d4b5e744c3a5317a9672))
* docker container failing to build ([9d27b94](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/9d27b94bccbafe958f66805f46d45e313eca875e))
* docker img to 3.11 ([fd63abb](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/fd63abb09097fe4e0884bff248edf49ad528d45d))
* issue with install command ([2302f7f](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/2302f7f18698c0cfc35a4989cbc1aec410c10199))
* remove websocket handle ([23396bd](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/23396bd2a68cffb4f4853bdedf77676d09ed4ebf))
* update readme ([b498ef0](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/b498ef096956408267ea87747d0f802106a0d286))


### 🧑‍💻 Code Refactoring

*  update README ([a71619a](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/a71619a11a27adb9899e98f78ae9b10c935bcc8d))


### 🔁 Continuous Integration

* **ci-fix:** fix ci pathing issue ([d986f71](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/d986f717a4d36d033cb8ccd8243edff8469b5585))
* **ci-fix:** fix location of ci script ([acce763](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/acce7639ee277eb1d60fb405c07c866448d9bd39))
* **ci-fix:** fix semantic-relase dependancy ([37f924b](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/37f924b345bc5d6a2005f05cf6a174e9e92f62a6))
* **ci-fix:** fix semantic-relase dependancy ([630d65b](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/630d65b8c05838b06a422287c367881fc061c5f1))
* **ci-fix:** fix semantic-relase dependancy ([5f9b4a1](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/5f9b4a17d7d355299efadd4fd51b54591b7fdb7f))
* **ci-fix:** fix semantic-relase dependancy ([d2ab46f](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/d2ab46fa3fb44e6e00dc854429bc8a6d76c7180a))
* **ci-fix:** fix semantic-relase dependancy ([8e4f7e0](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/8e4f7e03ffc18372bfc004745e3c58d08236bbd6))
* Setup ci system ([355c24b](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/355c24b17bfca2bdea05094767b79e59b214ccd2))
* Setup ci system ([9bb68a1](https://github.com/ZanzyTHEbar/ETVR-Tracking-Backend/commit/9bb68a1f599d06b644c975f64f8f66a5e1d440bb))
