# D2 Seerr run — files kept out of git (local only), path + SHA-256

Seerr settings copies (contain the public test apiKey 'testkey' / sessionSecret from cypress/config/settings.cypress.json), SQLite copies, admin session cookie, pid, and the demo scenario scratch copy are not committed. Hashes below reproduce the record; SHA256SUMS_seed / SHA256SUMS_snapshot hold the same values.

```
2fc1c4477de6309c2d9c3748e149831cc07bb65a4e89508ff9b6e6b64b73e70c  seed/settings.json
26ea1a14dbaa32d63658664f6da52b9cf003af3b33a645fb15c1e3cb8b907b50  seed/settings.after_first_start.json
520ffc0352fffac18226b0a93c8c77aa3331782f19b1de06df8af82520a8f24f  seed/db.before_seed.sqlite3
c77b8e89c9dea3d5c53c59885f28e369095853ee13a8e839f27330db7a86173d  seed/db.seeded.sqlite3
dcc9bfd751538657feb3769664b64d4e453f0abe87c684a671acf30afb91b02d  snapshot/db.sqlite3
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  snapshot/db.sqlite3-wal
fd4c9fda9cd3f9ae7c962b0ddf37232294d55580e1aa165aa06129b8549389eb  snapshot/db.sqlite3-shm
(not hashed)  logs/cookie_admin.txt  — Seerr admin session cookie from the local login test
(not hashed)  blade/admin_8102.pid
(not hashed)  ../demo_v7_runtime/scenario_run/  — scratch copy of the v7 demo policy store used by scenario_manual_to_owner.sh (contains tokens.json with test JWTs)
```
