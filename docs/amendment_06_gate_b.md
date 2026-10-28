# Báo cáo Gate B — 06-HO2 revision 3 (nhãn vẫn đóng)

Ngày: 2026-10-29. Commit mã đã khóa trước khi tạo báo cáo: `ce5ed204ca4125e93a423f72bd6efe3d4ec2d7cb`. **Không mở HO2; Phase C chưa bắt đầu.** Không chạy `scripts/evaluate_holdout2_once.py` hoặc `scripts/evaluate_test_once.py`.

## (a) Hash đối chiếu trực tiếp

SHA-256 lock mới: `42e044da1bda300f1fa521fcaf9530b08acc9864ef0be303ae26250c7db4abde`; revision=`3`; supersedes `193998064725a5d71b07b49edc5c4fb046e08b5292a86dd4649cf23f47c60880`; 85 hash nguồn.

| File | SHA-256 file thật | SHA-256 trong lock | Đối chiếu |
|---|---|---|---|
| `.gitignore` | `d09f804eae7a8600ee6b8a6b04d70be1f9f1fdabae6f50259d11a88955007e60` | `d09f804eae7a8600ee6b8a6b04d70be1f9f1fdabae6f50259d11a88955007e60` | khớp |
| `config/amendment_05_gift_lines.yaml` | `27bda2f81cfc963921ecb7a0da235777031996b26563d6425fbfa8d525eed720` | `27bda2f81cfc963921ecb7a0da235777031996b26563d6425fbfa8d525eed720` | khớp |
| `config/amendment_06_ho2.yaml` | `51713add5f3b09a0340e2b87ba2639567cd2567faf7c8d4ab1242bacd3c44342` | `51713add5f3b09a0340e2b87ba2639567cd2567faf7c8d4ab1242bacd3c44342` | khớp |
| `config/split.lock.json` | `cb6d983a9b32f43bfcbb671f7d71af1b012a70b8af999efbed3691ceb3e04440` | `cb6d983a9b32f43bfcbb671f7d71af1b012a70b8af999efbed3691ceb3e04440` | khớp |
| `config/split.yaml` | `38d0e35ee8b34016d1246d111eed0315974390ab255daee8b48002373331553e` | `38d0e35ee8b34016d1246d111eed0315974390ab255daee8b48002373331553e` | khớp |
| `docs/amendment_log.md` | `f6753dfee3c06562cce4ca96858e2477f7f2a3d680c3a6a59ef328eeb01f3b49` | `f6753dfee3c06562cce4ca96858e2477f7f2a3d680c3a6a59ef328eeb01f3b49` | khớp |
| `docs/analysis_plan_amendment06_ho2.md` | `59d277b42dc355ff0a193c359b230fa69d64a0d922aa8b56fe68dcfc9567a9ab` | `59d277b42dc355ff0a193c359b230fa69d64a0d922aa8b56fe68dcfc9567a9ab` | khớp |
| `docs/analysis_plan_gateb_r2.md` | `ff8c823e1989e536f75b8ed09a3fc399e3c10af041d678c4672e254ec198be8e` | `ff8c823e1989e536f75b8ed09a3fc399e3c10af041d678c4672e254ec198be8e` | khớp |
| `docs/analysis_plan_gateb_r4.md` | `b6dac1cd2efd64dcd11f92a93d5570a6e7c2330d7d1db0d9f34c0a23c252e85c` | `b6dac1cd2efd64dcd11f92a93d5570a6e7c2330d7d1db0d9f34c0a23c252e85c` | khớp |
| `docs/analysis_plan_gateb_r5.md` | `e9195f75d76a1326c816b7ebb67e4051771d0b77d9883b42404ced0c3861a6e9` | `e9195f75d76a1326c816b7ebb67e4051771d0b77d9883b42404ced0c3861a6e9` | khớp |
| `docs/analysis_plan_gateb_r6_fix.md` | `bb1de6adf63dd0bfa31211d44e307bc1d57652c5a0e97221ffc93d32c5308675` | `bb1de6adf63dd0bfa31211d44e307bc1d57652c5a0e97221ffc93d32c5308675` | khớp |
| `docs/analysis_plan_wp5.md` | `ebf26802ce20814c93d836c0b67e6c17a8ce53d5e65d23b56622bd034cf5e94f` | `ebf26802ce20814c93d836c0b67e6c17a8ce53d5e65d23b56622bd034cf5e94f` | khớp |
| `docs/analysis_plan_wp5b.md` | `ed9af7f35e03a41f2462462361f8476ba2b25dee89c6cd59340512419fcdd931` | `ed9af7f35e03a41f2462462361f8476ba2b25dee89c6cd59340512419fcdd931` | khớp |
| `docs/analysis_plan_wp5c.md` | `8dd4774425659f170de08669d42b2d358cdd6c2ed4cd5a33ed68ebeb6767fbf8` | `8dd4774425659f170de08669d42b2d358cdd6c2ed4cd5a33ed68ebeb6767fbf8` | khớp |
| `docs/canonical_numbers.md` | `6af06bc7e3f2083dcac01c2f0553965b9b9fc2133b9026bc39e32395bd193bc8` | `6af06bc7e3f2083dcac01c2f0553965b9b9fc2133b9026bc39e32395bd193bc8` | khớp |
| `docs/cohort_definitions.md` | `2c967bab229509a5d812c8a6102387aca37ad72c23ee57c226941ef3df488ace` | `2c967bab229509a5d812c8a6102387aca37ad72c23ee57c226941ef3df488ace` | khớp |
| `docs/decisions.md` | `0f8e29eba0f8c89cea7ff7453686bc93cd69fd2cd3e4025e8bac76236cb95fa3` | `0f8e29eba0f8c89cea7ff7453686bc93cd69fd2cd3e4025e8bac76236cb95fa3` | khớp |
| `docs/gateb_r2_results.md` | `f5cc8c5a0dffe52381be7ed9bbfcba75852de9d25ff29e2df49f4b881b4460e2` | `f5cc8c5a0dffe52381be7ed9bbfcba75852de9d25ff29e2df49f4b881b4460e2` | khớp |
| `docs/gateb_r4_results.md` | `d8ee4e2972a8b54e80099382f8ec72a912bbfa1d91cd647efa4cbcaa5f6831ce` | `d8ee4e2972a8b54e80099382f8ec72a912bbfa1d91cd647efa4cbcaa5f6831ce` | khớp |
| `docs/gateb_r5_results.md` | `1f8a4949ef4157cfe6fc518630adfd41bede67fac635cec687f8ed0a00406803` | `1f8a4949ef4157cfe6fc518630adfd41bede67fac635cec687f8ed0a00406803` | khớp |
| `docs/ho2_access_audit.md` | `c97ea3640061fd1c9b551fa6bd5fcc1866e32bb3bead77afe74b444f18624d16` | `c97ea3640061fd1c9b551fa6bd5fcc1866e32bb3bead77afe74b444f18624d16` | khớp |
| `docs/test_provenance_note.md` | `f00531f80169008ccf07902fe4a76ec337938742995a5c5d67e377e28a64646b` | `f00531f80169008ccf07902fe4a76ec337938742995a5c5d67e377e28a64646b` | khớp |
| `outputs/logs/test_eval_access.jsonl` | `2061ddbc30ca89ee48a7df2530bc29aa0b0fe335a76ff1b37fdd8c2903edebc9` | `2061ddbc30ca89ee48a7df2530bc29aa0b0fe335a76ff1b37fdd8c2903edebc9` | khớp |
| `outputs/metrics/day3_pretest_freeze.json` | `be57e7a73fb0844ac46ebd3707e65db5008f0cc23f57c46c93afd40bf975727d` | `be57e7a73fb0844ac46ebd3707e65db5008f0cc23f57c46c93afd40bf975727d` | khớp |
| `outputs/metrics/dev_final_model.json` | `7b0002e4d7c6b61a0b8929dd4af80b47a4a43ed352a066de508167fe97958221` | `7b0002e4d7c6b61a0b8929dd4af80b47a4a43ed352a066de508167fe97958221` | khớp |
| `outputs/metrics/dev_final_models_v2.json` | `27c2f011a52bf45816b82153270db56522b639c0aada82e777ace1d0611b5c83` | `27c2f011a52bf45816b82153270db56522b639c0aada82e777ace1d0611b5c83` | khớp |
| `outputs/metrics/frozen_segmenters_dev.json` | `307e6ced38704c5e29789cf503ceb1a8c3d19f14d8318db1707c5624fb3d3b0c` | `307e6ced38704c5e29789cf503ceb1a8c3d19f14d8318db1707c5624fb3d3b0c` | khớp |
| `outputs/metrics/gateb_r2_power.json` | `8a8113db17c6bc59b53c806f4790f727905c0d663807059fbab141ba2d54031f` | `8a8113db17c6bc59b53c806f4790f727905c0d663807059fbab141ba2d54031f` | khớp |
| `outputs/metrics/gateb_r2_rr_dev.json` | `ac0572eb47fe43d9768a8ae0b7bd783839d573a852b7f05f3127b82fda474d37` | `ac0572eb47fe43d9768a8ae0b7bd783839d573a852b7f05f3127b82fda474d37` | khớp |
| `outputs/metrics/gateb_r4_dev_calibration.json` | `60617a9c181d0cd583687d69f84adeba5203c967095d152308d904cd00f127b5` | `60617a9c181d0cd583687d69f84adeba5203c967095d152308d904cd00f127b5` | khớp |
| `outputs/metrics/gateb_r5_strategy_freeze.json` | `bfac6b9d057189d9655693248532a673e0d2c4c85721a0214a0f7fc9a668cbee` | `bfac6b9d057189d9655693248532a673e0d2c4c85721a0214a0f7fc9a668cbee` | khớp |
| `outputs/metrics/repurchase_v3_dev.json` | `9cce1e1a55a333d92b1295723a805876b25055491abb91ce4f8c0c122d2a2d26` | `9cce1e1a55a333d92b1295723a805876b25055491abb91ce4f8c0c122d2a2d26` | khớp |
| `outputs/metrics/repurchase_wp5b_dev.json` | `c618812b21e90237f61ac63555ab533e673b6a44e0020c02b23d53c660b3b3ff` | `c618812b21e90237f61ac63555ab533e673b6a44e0020c02b23d53c660b3b3ff` | khớp |
| `outputs/metrics/repurchase_wp5c_dev.json` | `03fc1a143897f3e69cc7356ba66f2722df231cc26fbf0d56a9a91128c8fc3c62` | `03fc1a143897f3e69cc7356ba66f2722df231cc26fbf0d56a9a91128c8fc3c62` | khớp |
| `outputs/metrics/test_eval.json` | `5b502637d05f4a21cfa803b3f1582c8d507335e2dcac64ee63d84826f123c625` | `5b502637d05f4a21cfa803b3f1582c8d507335e2dcac64ee63d84826f123c625` | khớp |
| `outputs/metrics/test_opened.lock.json` | `74af2c6ccd61f6c071529115b13ff144b25fa264600cb27e1832f764bde6d874` | `74af2c6ccd61f6c071529115b13ff144b25fa264600cb27e1832f764bde6d874` | khớp |
| `outputs/models/day2_dev_final_model.joblib` | `0ac767d24c641f50bdc19634e590dc45a92d9e4cd5513d02871fac50b109cd4a` | `0ac767d24c641f50bdc19634e590dc45a92d9e4cd5513d02871fac50b109cd4a` | khớp |
| `outputs/models/gateb_r5/s3_final_dev.joblib` | `63e47afbe0a1ef73c01d0be2974c354d753a7299f3d1952146b91bd8b2d1706b` | `63e47afbe0a1ef73c01d0be2974c354d753a7299f3d1952146b91bd8b2d1706b` | khớp |
| `outputs/models/gateb_r5/s6_final_dev.json` | `17af23fa3a84a40c357856271489badd6a1061fd15cac62ace1573627b64d048` | `17af23fa3a84a40c357856271489badd6a1061fd15cac62ace1573627b64d048` | khớp |
| `outputs/models/gateb_r5/v3_final_dev.joblib` | `fc04ee70693da1a1e16350b99acf80b335705000dac35ba67bde63ef9c5d348b` | `fc04ee70693da1a1e16350b99acf80b335705000dac35ba67bde63ef9c5d348b` | khớp |
| `outputs/models/repurchase_features_v2.joblib` | `5cbe48bb9b4944d91dfba7b85dd5d1608eb836b68574b16d3ac6a6319f8a2f80` | `5cbe48bb9b4944d91dfba7b85dd5d1608eb836b68574b16d3ac6a6319f8a2f80` | khớp |
| `outputs/models/segmenters_dev_frozen_v1.joblib` | `5babaa2352921f840385bdfe6681948f329b0ee276de2aef1cc8500c9146b93f` | `5babaa2352921f840385bdfe6681948f329b0ee276de2aef1cc8500c9146b93f` | khớp |
| `outputs/tables/combo_recommendation_screen_f3.csv` | `75069387d808a96fd35b2a0e06b843f4ff04ff01d78a9846d3d6f7b482220b9c` | `75069387d808a96fd35b2a0e06b843f4ff04ff01d78a9846d3d6f7b482220b9c` | khớp |
| `outputs/tables/combos_v2.csv` | `ae7df8760857a9a7aa2cd667704829e71b076a70b5ca2f0a41fd6396ef0538d6` | `ae7df8760857a9a7aa2cd667704829e71b076a70b5ca2f0a41fd6396ef0538d6` | khớp |
| `outputs/tables/repurchase_wp5c_train_rates.csv` | `be2845bbd7020c0241aecf36412a8eaa123d3a7fcdbb58070026ec184d3232a3` | `be2845bbd7020c0241aecf36412a8eaa123d3a7fcdbb58070026ec184d3232a3` | khớp |
| `scripts/analyze_gateb_r2_dev.py` | `a10e17b41abab68209a439d3f0e7a3589c114139563c7244e227234233cede5f` | `a10e17b41abab68209a439d3f0e7a3589c114139563c7244e227234233cede5f` | khớp |
| `scripts/audit_committed_aggregate_dates.py` | `3e758ce088e573bc9883fbbd8bf253798636accb97f8973828ef677e69dc82ed` | `3e758ce088e573bc9883fbbd8bf253798636accb97f8973828ef677e69dc82ed` | khớp |
| `scripts/build_amendment06_gateb_report.py` | `7ec1459857947140cb069eb37507775900cc99d4742a4921ff9cc819c52cb92a` | `7ec1459857947140cb069eb37507775900cc99d4742a4921ff9cc819c52cb92a` | khớp |
| `scripts/build_amendment06_lock.py` | `49f00f4966be492bf53f4fa083e5e07428c947f94f7f9669565ffc582313722a` | `49f00f4966be492bf53f4fa083e5e07428c947f94f7f9669565ffc582313722a` | khớp |
| `scripts/build_amendment06_revision_log.py` | `fa77520d2753330faa8fcb9e78a19c370476d8d4c84b988d58a9d980545d8e28` | `fa77520d2753330faa8fcb9e78a19c370476d8d4c84b988d58a9d980545d8e28` | khớp |
| `scripts/calibrate_gateb_r4_dev.py` | `9c65803bce23c294b689110b96e5fa6051aff1dd13a44dad98deb76073a01282` | `9c65803bce23c294b689110b96e5fa6051aff1dd13a44dad98deb76073a01282` | khớp |
| `scripts/count_ho2_eligibility_preregistered.py` | `e6cf124588dc7791fdaf7131c91246a125642ca4d3f7c343362f48ed4be25a10` | `e6cf124588dc7791fdaf7131c91246a125642ca4d3f7c343362f48ed4be25a10` | khớp |
| `scripts/evaluate_holdout2_once.py` | `08ae2147ab7704d0f758a548d95a083e1bb6b577ab3395e3ff5cad631dab2ed0` | `08ae2147ab7704d0f758a548d95a083e1bb6b577ab3395e3ff5cad631dab2ed0` | khớp |
| `scripts/evaluate_repurchase_wp5b_dev.py` | `99e68c6d1c57ab1595339a72787d385e7fae73d5243e4a561c0fed56969951a4` | `99e68c6d1c57ab1595339a72787d385e7fae73d5243e4a561c0fed56969951a4` | khớp |
| `scripts/evaluate_repurchase_wp5c_dev.py` | `6a95efeb8465e30f28cbfc6120a7afb41762c04cfa41a77b247750acd128c676` | `6a95efeb8465e30f28cbfc6120a7afb41762c04cfa41a77b247750acd128c676` | khớp |
| `scripts/fix_sealed_eol.py` | `8c9ae853370e33f0d089843e6799a24b861db7665805f5214d5d063815c65e06` | `8c9ae853370e33f0d089843e6799a24b861db7665805f5214d5d063815c65e06` | khớp |
| `scripts/freeze_gateb_strategies_dev.py` | `984740129ebc9abe5ad7ba727f40950d5413fd3658823caa94f66b118ee6719d` | `984740129ebc9abe5ad7ba727f40950d5413fd3658823caa94f66b118ee6719d` | khớp |
| `scripts/run_all.py` | `c28c211413329602834f890be345ed141e396b34ea0a9a87c908fa7972b86b3c` | `c28c211413329602834f890be345ed141e396b34ea0a9a87c908fa7972b86b3c` | khớp |
| `scripts/summarize_gateb_r2_power.py` | `15913f5a2b67a8d8bb61be405f9207a470905ca741c2f597356f6475299a64c0` | `15913f5a2b67a8d8bb61be405f9207a470905ca741c2f597356f6475299a64c0` | khớp |
| `scripts/summarize_ho2_power.py` | `597098df598d8ad7b7ede5c74be99fcfb6f245cf1f74e9fe2b2e913b4970bb01` | `597098df598d8ad7b7ede5c74be99fcfb6f245cf1f74e9fe2b2e913b4970bb01` | khớp |
| `scripts/verify_day3_locks.py` | `0e43a87aecca3482a1c7b61fe7001f4437ed7c1deeab21cf40c47d4dab52eead` | `0e43a87aecca3482a1c7b61fe7001f4437ed7c1deeab21cf40c47d4dab52eead` | khớp |
| `scripts/verify_gateb_lock.py` | `967e71f8f9522145b101db11b430cea2022204841ed2d167bfc9c44e2c9cf76d` | `967e71f8f9522145b101db11b430cea2022204841ed2d167bfc9c44e2c9cf76d` | khớp |
| `scripts/verify_pii.py` | `5de909685ce13ab7d14166b00f35dc3534d76c785ce6ee7c1d59f96ef7ac1001` | `5de909685ce13ab7d14166b00f35dc3534d76c785ce6ee7c1d59f96ef7ac1001` | khớp |
| `scripts/verify_readonly.py` | `a9497845f36a54f892312d8e80bc3487e12062b2bc15840926b732277f837d87` | `a9497845f36a54f892312d8e80bc3487e12062b2bc15840926b732277f837d87` | khớp |
| `src/features/day2_data.py` | `c8091e7faa4f59f644994ba471fcbc565a1a72878f793044f433f136dba3d52f` | `c8091e7faa4f59f644994ba471fcbc565a1a72878f793044f433f136dba3d52f` | khớp |
| `src/features/day2b_data.py` | `2e8c79c79a0aef51ec522542e4c6e9879317c3d72027c79cf7825d75fa9147fe` | `2e8c79c79a0aef51ec522542e4c6e9879317c3d72027c79cf7825d75fa9147fe` | khớp |
| `src/features/gift_lines.py` | `be43bb7caa54a240f60c890e9f56bbdd2c6b537ced8eb60cc9be5ce889385dd0` | `be43bb7caa54a240f60c890e9f56bbdd2c6b537ced8eb60cc9be5ce889385dd0` | khớp |
| `src/features/holdout2_access.py` | `93afe62323ab10ddb5e90889486b6acc018adcc83a8931b22bd4f1590651359c` | `93afe62323ab10ddb5e90889486b6acc018adcc83a8931b22bd4f1590651359c` | khớp |
| `src/features/holdout2_features.py` | `826c5085a2b3fe0315a4f8501b13155e5f6b4ed6eb6db3e07f5639f1a72f8eac` | `826c5085a2b3fe0315a4f8501b13155e5f6b4ed6eb6db3e07f5639f1a72f8eac` | khớp |
| `src/features/holdout2_metrics.py` | `b2f4b36423171315838beef110ca32c2ee0bf2a3809effea3157278ea60d0c1c` | `b2f4b36423171315838beef110ca32c2ee0bf2a3809effea3157278ea60d0c1c` | khớp |
| `src/features/money.py` | `7a22b4da01bdb1c2ca31f5d1a3089177dbd0838ead2c417b9abd828d4b668a3f` | `7a22b4da01bdb1c2ca31f5d1a3089177dbd0838ead2c417b9abd828d4b668a3f` | khớp |
| `src/features/repurchase_v3.py` | `332f62cd7b6d4737c9783add6e35476b32b75925a153583cad3104484a489398` | `332f62cd7b6d4737c9783add6e35476b32b75925a153583cad3104484a489398` | khớp |
| `src/ingest/identifiers.py` | `66de4a07a4af32d9d3dda49357f181ec3f242e56be1100d115ba8356590e9dd4` | `66de4a07a4af32d9d3dda49357f181ec3f242e56be1100d115ba8356590e9dd4` | khớp |
| `src/ingest/settings.py` | `1c8bc9900b97901c13fba834e5379e7d57f8cc418af344605ce16f660f6442a6` | `1c8bc9900b97901c13fba834e5379e7d57f8cc418af344605ce16f660f6442a6` | khớp |
| `src/models/classify.py` | `35ed02908eeeec0a4ce89893ee1aa0c439bb30eb8e1c47d30609975c66de46fa` | `35ed02908eeeec0a4ce89893ee1aa0c439bb30eb8e1c47d30609975c66de46fa` | khớp |
| `src/models/classify_v2.py` | `eab950787f56bd42016ceb6c05156946e1b969edc3b73e3b6b3f8a9712642301` | `eab950787f56bd42016ceb6c05156946e1b969edc3b73e3b6b3f8a9712642301` | khớp |
| `src/models/frozen_segmenters.py` | `1c56234602933d495b0ef5bc665bd4b4f76d9f17a9e8a01320117fb88eae65cf` | `1c56234602933d495b0ef5bc665bd4b4f76d9f17a9e8a01320117fb88eae65cf` | khớp |
| `src/models/repurchase_v3.py` | `5bf2a685bce70eedff52fe595ceb1475bb4bf372aaab3b452ae59dfd7372f3b3` | `5bf2a685bce70eedff52fe595ceb1475bb4bf372aaab3b452ae59dfd7372f3b3` | khớp |
| `tests/test_gateb_aggregate_date_audit.py` | `f751fe5090024620e4db41e059fa66a5b3303939a34e6e56d6f40fc5982c8041` | `f751fe5090024620e4db41e059fa66a5b3303939a34e6e56d6f40fc5982c8041` | khớp |
| `tests/test_gateb_lock_verification.py` | `582bd4b276598c01343581332290efdfbfcc8afd99a6d023026d2878e6c202c4` | `582bd4b276598c01343581332290efdfbfcc8afd99a6d023026d2878e6c202c4` | khớp |
| `tests/test_gateb_r4_calibration.py` | `dec6c98324f26920588db30aeedc158ab7b182349446892ebf665165a5e754c4` | `dec6c98324f26920588db30aeedc158ab7b182349446892ebf665165a5e754c4` | khớp |
| `tests/test_gateb_r5_freeze.py` | `79843a63f32bdc279d059effd4da9890bf71f2fbdefd26eda76f0a13de9d76e0` | `79843a63f32bdc279d059effd4da9890bf71f2fbdefd26eda76f0a13de9d76e0` | khớp |
| `tests/test_gateb_report_hashes.py` | `16197f7b6fb1c43796485e2ffb276624102d401c7c52e1bb5a025dfa71bda6ff` | `16197f7b6fb1c43796485e2ffb276624102d401c7c52e1bb5a025dfa71bda6ff` | khớp |
| `tests/test_holdout2_feature_boundary.py` | `3ea31c9975fc597e5176f19fa119112e9687bec3d275063f4bdcb6a287cc14cd` | `3ea31c9975fc597e5176f19fa119112e9687bec3d275063f4bdcb6a287cc14cd` | khớp |
| `tests/test_holdout2_metrics.py` | `34d9cbe5a403c871bd82dc132617232dec37743b15b76df741e3b4f80dbf0811` | `34d9cbe5a403c871bd82dc132617232dec37743b15b76df741e3b4f80dbf0811` | khớp |

## (b) G1 — chẩn đoán số và thứ tự preregistration/code

Evaluator rev2 (`scripts/evaluate_holdout2_once.py::_h4_eval`, dòng 282–286) dùng `scipy.stats.spearmanr(...).statistic` rồi so sánh trực tiếp `rho >= threshold`; chưa có dung sai. Dữ liệu tổng hợp, không dùng HO2:

| Ca tổng hợp | n | rho | Ngưỡng | rho−ngưỡng | So sánh cũ | So sánh rev3 (−1e-9) |
|---|---:|---:|---:|---:|---|---|
| S6, một swap liền kề, SciPy spearmanr | 8 | `0.97619047619047628` | `0.97619047619047628` | `0` | PASS | PASS |
| S6, hai swap liền kề, SciPy spearmanr | 8 | `0.95238095238095244` | `0.97619047619047628` | `-0.023809523809523836` | FAIL | FAIL |
| S6, một ULP dưới ngưỡng (synthetic float) | 8 | `0.97619047619047616` | `0.97619047619047628` | `-1.1102230246251565e-16` | FAIL | PASS |
| RFM, thứ hạng đồng nhất, SciPy spearmanr | 6 | `1` | `1` | `0` | PASS | PASS |
| RFM, 1−1e−16 (synthetic float) | 6 | `0.99999999999999989` | `1` | `-1.1102230246251565e-16` | FAIL | PASS |
| RFM, một swap liền kề, SciPy spearmanr | 6 | `0.94285714285714295` | `1` | `-0.057142857142857051` | FAIL | FAIL |

Với đúng SciPy hiện cài, ca S6 một swap trả `0.9761904761904763` và phép so cũ vẫn PASS; vì vậy không tái hiện lỗi trong hoán vị đó ở runtime này. Giá trị đóng `1−12/504` có thể thành `0.9761904761904762`; hàng ULP cho thấy phép so trực tiếp trượt, còn dung sai chỉ hấp thụ sai số rất nhỏ. Hai swap và một swap RFM vẫn trượt. Ngưỡng giữ nguyên; tối thiểu 4 nhóm giữ nguyên.
Sai khác đã ghi nhận: plan G1 (commit `384d565`) dự kiến hai swap liền kề cho rho `0.9047619`; test đã định nghĩa hai phép đổi cặp liền kề độc lập và SciPy cho `0.9523810`. Bốn phép đổi cặp cho `0.9047619`. Đây là sai số ở con số dự kiến trong plan, không làm đổi tiêu chí; file preregistration được giữ nguyên và sai khác được công khai tại đây.

Thứ tự commit từ Gate B rev2:
- `384d565 2026-10-29T00:36:32+07:00 Preregister Gate B H4 tolerance fix`
- `9ddbc70 2026-10-29T00:45:31+07:00 Harden Gate B H4 floating point threshold`
- `ce5ed20 2026-10-29T00:48:10+07:00 Clarify Gate B revision 3 audit records`
Timestamp là metadata Git, không phải bằng chứng bất biến về thứ tự thời gian.

## (c) Nhật ký thay đổi revision 3

Từng file, SHA-256 cũ/mới và lý do cụ thể nằm trong [amendment_06_revision_log.md](amendment_06_revision_log.md). Lock rev2 bị supersede bằng đúng hash ghi trên.

R5 JSON comparison: historical version at `a052bae` and current DEV freeze differ only by `standardizer_mean`/`standardizer_scale` on recency-only and frequency-only; the log reports raw-byte and normalized-LF SHA-256. All remaining JSON fields match. This records scaling for descriptive scores; coefficient signs, recipe, outcomes and model-selection decisions are unchanged. No HO2 labels were used.
Commit `94a1fae` also changed `docs/canonical_numbers.md` (added standardizer means/scales), `docs/gateb_r5_results.md` (reported those values) and `scripts/freeze_gateb_strategies_dev.py` (serialized scaler means/scales).

## (d) R2 — H2 trở lại giả thuyết chính

DEV snapshot-weighted RR frequency≥2 / frequency=1 = **3.473**, bootstrap CI 95% **[2.656; 4.520]**; nhóm frequency=1: 780/19442 dương/snapshot; frequency≥2: 306/2196. Khám phá DEV-only, chưa xác nhận ngoài mẫu.

### H1 power: AUC thật so với ngưỡng 0,55

| Mốc prevalence | AUC giả định | Công suất |
|---|---:|---:|
| DEV 7,4% | 0.55 | 0.0250 |
| DEV 7,4% | 0.60 | 0.9638 |
| DEV 7,4% | 0.65 | 1.0000 |
| DEV 7,4% | 0.70 | 1.0000 |
| Aggregate test cũ 4,6% | 0.55 | 0.0250 |
| Aggregate test cũ 4,6% | 0.60 | 0.8499 |
| Aggregate test cũ 4,6% | 0.65 | 1.0000 |
| Aggregate test cũ 4,6% | 0.70 | 1.0000 |

### H2 power: RR thật so với ngưỡng 1,5

| Mốc prevalence | RR giả định | Công suất |
|---|---:|---:|
| DEV 7,4% | 1.500000 | 0.0250 |
| DEV 7,4% | 2.000000 | 0.8570 |
| DEV 7,4% | 2.500000 | 0.9999 |
| DEV 7,4% | 3.000000 | 1.0000 |
| DEV 7,4% | 2.656091 | 1.0000 |
| Aggregate test cũ 4,6% | 1.500000 | 0.0250 |
| Aggregate test cũ 4,6% | 2.000000 | 0.6443 |
| Aggregate test cũ 4,6% | 2.500000 | 0.9923 |
| Aggregate test cũ 4,6% | 3.000000 | 1.0000 |
| Aggregate test cũ 4,6% | 2.656091 | 0.9987 |

Quy tắc đăng ký R2: công suất ở RR=cận dưới DEV 2.656 là 100.00% (DEV) và 99.87% (aggregate test cũ), đều ≥80%; H2 là chính. Hai kiểm định chính H1/H2 dùng Holm step-down 0,025/0,05. Bảng đầy đủ và giới hạn trong `docs/gateb_r2_results.md`.

## (e) R5 — chiến lược và quần thể fit

| Chiến lược | Trạng thái | Quần thể fit / mô tả | SHA-256 artifact |
|---|---|---|---|
| S1 | đủ điều kiện | fixed rule, no fit | `—` |
| S3 | đủ điều kiện | all DEV multi-snapshot | `63e47afbe0a1ef73c01d0be2974c354d753a7299f3d1952146b91bd8b2d1706b` |
| S6 | đủ điều kiện | all DEV multi-snapshot | `17af23fa3a84a40c357856271489badd6a1061fd15cac62ace1573627b64d048` |
| D-005 | đủ điều kiện | pre-existing frozen DEV artifact; not refit | `0ac767d24c641f50bdc19634e590dc45a92d9e4cd5513d02871fac50b109cd4a` |
| v2 | đủ điều kiện | pre-existing frozen DEV artifact; not refit | `5cbe48bb9b4944d91dfba7b85dd5d1608eb836b68574b16d3ac6a6319f8a2f80` |
| v3 | đủ điều kiện | all DEV multi-snapshot | `fc04ee70693da1a1e16350b99acf80b335705000dac35ba67bde63ef9c5d348b` |
| recency_only | đủ điều kiện | DEV score rule; hệ số -0.46545; dấu -1 | `—` |
| frequency_only | đủ điều kiện | DEV score rule; hệ số +0.42799; dấu +1 | `—` |

S3, S6, v3 theo phương án A: final-fit toàn DEV đa mốc. `repurchase_wp5c_train_rates.csv` là mapping theo fold train, không phải quần thể final-fit. D-005 giữ mô hình chính.

## (f) Tiêu chí H1–H5 cuối

- **H1:** D-005 ROC-AUC>0,55; một phía bootstrap 2.000 khách, Holm với H2. Đạt khi AUC điểm vượt ngưỡng và p Holm<0,05. Chênh `AUC−0,70` chỉ mô tả, kèm CI. Đạt H1 không có nghĩa lặp lại AUC test 0,70.
- **H2:** RR mua lại 180 ngày frequency≥2/frequency=1>1,5; CI bootstrap theo khách, p bootstrap một phía tại RR=1,5; Holm cùng H1.
- **H3:** S1/S3/S6 × precision@10/lift (6 phép so sánh phụ, không hiệu chỉnh). Tie-aware: K=ceil(0,10N), q=(K−n_above)/n_tie, precision=(pos_above+q×pos_tie)/K, lift=precision/prevalence. Hỗ trợ nếu cận dưới CI95 precision>prevalence và lift>1. S1 nhị phân, S3/S6 điểm rời rạc; ROC/decile chỉ mô tả.
- **H4:** Spearman S6/RFM DEV-pooled so với HO2; n≥30, tối thiểu 4 nhóm chung. Ngưỡng giữ nguyên S6 `0.9761904761904763`; RFM `1.0`; so sánh `rho ≥ threshold−1e-9`. Ngưỡng không đổi nếu n nhóm khác 8/6; đó là giới hạn đã biết.
- **H5:** 24 combo đóng băng; `k_DEV=1`, chỉ mô tả vì k<4. Giỏ status 3 không quà, `T2<date≤T2+180`, bỏ gift line, ≥2 product IDs; cặp <30 bị che và không tính qua bộ lọc.
- **H6:** không kiểm định; DEV không có dải xu hướng đáng tin đã đăng ký trước.

## (g) Kiểm thử và dry-run

- `run_all.py`: xanh; `pytest`: **171 passed**. PII scan, verify lock và dashboard smoke xanh.

| Test mới | Kiểm tra | Kết quả |
|---|---|---|
| `test_gateb_r4_calibration_uses_registered_cells_and_counts_dev_combo_filter` | H4 nhóm cố định; H5 k_DEV filter DEV | PASS |
| `test_gateb_r5_univariate_direction_comes_from_dev_fit` | chiều recency/frequency theo dấu hệ số | PASS |
| `test_temporal_parser_orders_dates_and_partials` | parser ngày/tháng/quý aggregate | PASS |
| `test_csv_audit_reads_only_temporal_column` | scanner chỉ trả cột thời gian | PASS |
| `test_metrics_match_hand_calculation` | ROC-AUC, RR, tie-aware precision/lift | PASS |
| `test_holm_step_down_and_customer_cluster_bootstrap_are_deterministic` | Holm và bootstrap cụm khách | PASS |
| `test_centered_bootstrap_p_uses_registered_effect_threshold` | p bootstrap định tâm tại ngưỡng H1/H2 | PASS |
| `test_yaml_date_conditions_and_boundary_rows` | T2, T2+1, T2+180, T2+181 khớp YAML | PASS |
| `test_feature_builder_matches_existing_fixed_t_features_and_excludes_t_or_later` | feature D-005 khớp hàm cũ tại T; không dùng ngày >=T | PASS |
| `test_holdout2_loader_refuses_to_run_without_open_lock` | loader chặn khi chưa có lock | PASS |
| `test_dry_run_gate_accepts_only_full_dev_horizon_and_rejects_t2` | dry-run chỉ DEV horizon đủ | PASS |
| `test_open_lock_is_created_once_after_exact_owner_phrase` | phrase đúng, tạo một lần, lần hai bị từ chối | PASS |
| `test_closed_lock_verifies_all_required_hashes_and_outputs_absent` | lock hash/EOL/trạng thái đóng | PASS |
| `test_lock_verifier_rejects_hash_mutation_and_open_outputs` | từ chối hash sai hoặc output đã mở | PASS |
| `test_report_hash_table_matches_lock_and_file_bytes` | bảng hash report=lock=file thật | PASS |
| `test_hypothesis_lists_are_consistent_across_config_lock_and_protocol` | danh sách giả thuyết protocol/config/lock/report | PASS |
| `test_h4_spearman_tolerance_handles_preregistered_synthetic_boundaries` | S6/RFM rho gần ngưỡng; hai swap trượt; dưới 4 nhóm không testable | PASS |
| `test_report_includes_g1_diagnostics_g2_prevalence_and_g3_proposal` | report có bảng G1, ghi chú prevalence và đề xuất G3 | PASS |

- Dry-run: **mã chạy đúng**; T=2025-04-20; feature rows=3601; end=2025-10-17. Nhãn: “kiểm thử mã, không phải kết quả, không dùng để chọn hay tinh chỉnh”. Không có metric/AUC dry-run trong báo cáo.

## (h) Kiểm toán truy cập và aggregate

Audit đầy đủ tại [ho2_access_audit.md](ho2_access_audit.md): 89 aggregate CSV/JSON đã quét, 22 có trường thời gian; max ngày kho DuckDB `2025-10-21`; dashboard `2026-04` là tháng partial của test cũ; `2026-10-31` chỉ là lịch tham chiếu. Không thấy event aggregate sau T2. Giới hạn pháp y được ghi rõ.

## (i) Gate trạng thái

Lock revision 3: `prepared_gate_b_not_open`; `test_opened=false`; `phase_c_started=false`. Các hash nguồn khớp file thật tại thời điểm dựng báo cáo. Không tồn tại output mở HO2 trong checkout tại Gate B.

## (j) Phát hiện, rủi ro, và trạng thái công việc

Ba phát hiện chính: (1) H2 DEV RR=3,473, CI[2,656;4,520] và đủ công suất theo quy tắc đã đăng ký; (2) hiệu chuẩn H4 DEV nửa đầu/nửa sau cao nhưng chỉ 8 ô S6, 6 nhóm RFM; (3) `k_DEV=1`, nên H5 không thể là kiểm định xác nhận.

Rủi ro còn lại: một cửa hàng/snapshot hồi cứu; trạng thái đơn có thể thay đổi sau T2; CI không đảm bảo khái quát; metric quan sát không phải nhân quả/lợi nhuận; D-005/v2 có quy trình fit lịch sử khác S3/S6/v3. H6 chưa testable.

**G3 — đề xuất, chưa thực hiện:** giữ cả hai điều kiện H3 hiện tại cho đến khi chủ dự án quyết định. Nếu precision-CI và lift-CI dùng cùng prevalence cố định, cận dưới lift>1 tương đương cận dưới precision>prevalence; nhưng code bootstrap lift theo prevalence của từng draw nên CI hai đại lượng không phải phép biến đổi tuyến tính của nhau. Ví dụ tổng hợp: prevalence điểm 0,10, cận dưới precision 0,101 nhưng cận dưới lift 0,99 — điều kiện precision đạt, điều kiện lift không đạt. Giữ cả hai hiện tại bảo toàn prereg và tính thận trọng; đổi sang một điều kiện sẽ thay tiêu chí đã khóa.

Giả định prevalence: 7,4% và 4,6% lần lượt là tỷ lệ cấp khách 260/3.508 và 237/5.169. Số 539/335 là số dương kỳ vọng khi áp hai mốc đó lên 7.282 khách giả định trong power; không phải số quan sát. R2 dùng estimand snapshot 1.086/21.638 = 5,02%, khác cấp khách. Chưa kiểm tính chuyển prevalence sang HO2.

README hiện chưa mô tả Amendment 06/Gate B; hạn nộp `2026-10-27` đã qua. Không sửa README trong lượt này; chờ quyết định chủ dự án.

| Đã làm | Chưa làm | Cần quyết định của chủ dự án |
|---|---|---|
| G1/G2/G4, bổ sung ghi chú G3, lock/report rev3, revision log cụ thể | Mở HO2, chạy Phase C, cập nhật README | Có đổi tiêu chí H3; có chấp nhận H4 với n nhóm khác 8/6; có cập nhật README |

**Gate B revision 3 dừng tại đây.** Báo cáo này không phải yêu cầu hay sự cho phép mở HO2.
