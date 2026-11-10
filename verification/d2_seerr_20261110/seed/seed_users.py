"""Insert the two Seerr test users exactly as server/utils/seedTestDb.ts (v3.5.1, 564bfb08) does — no other values.

Source of every value: upstream/seedTestDb.ts (sha256 3ce54cf4…) lines 43-75; UserType.PLEX = 1 (upstream/user.ts);
avatar = gravatar-url@4.0.1 gravatarUrl(email, {default:'mm', size:200}) = https://gravatar.com/avatar/<md5(email)>?default=mm&size=200.
Run against a db.sqlite3 whose schema Seerr already created (container started once). Idempotent on email.
"""
import hashlib
import sqlite3
import sys

HASH = '$2b$12$Z5V2P5HZgmx4/AnWFMZN1.aD5AM1NucNi.mhNTSQ9oVtmdzu7Le/a'  # seedTestDb.ts line 18, bcrypt('test1234')
USERS = [  # (email, username/plexUsername, permissions)
    ('admin@seerr.dev', 'admin', 2),   # Permission.ADMIN
    ('demo@seerr.dev', 'demo', 32),    # Permission.REQUEST
]


def gravatar(email: str) -> str:
    return 'https://gravatar.com/avatar/' + hashlib.md5(email.strip().lower().encode()).hexdigest() + '?default=mm&size=200'


def main(db: str) -> None:
    con = sqlite3.connect(db)
    cols = {r[1] for r in con.execute('PRAGMA table_info(user)')}
    need = {'email', 'plexUsername', 'username', 'password', 'userType', 'plexId', 'plexToken', 'permissions', 'avatar'}
    missing = need - cols
    if missing:
        sys.exit(f'user table lacks columns {sorted(missing)}; schema not created yet?')
    admin_plex = con.execute('SELECT plexId FROM user WHERE id = 1').fetchone()
    plex_id = admin_plex[0] if admin_plex and admin_plex[0] is not None else 1  # seedTestDb: admin?.plexId ?? 1
    for email, name, perms in USERS:
        row = {'plexId': plex_id, 'plexToken': '1234', 'plexUsername': name, 'username': name, 'email': email,
               'userType': 1, 'password': HASH, 'permissions': perms, 'avatar': gravatar(email)}
        exists = con.execute('SELECT id FROM user WHERE email = ?', (email,)).fetchone()
        if exists:
            con.execute('UPDATE user SET ' + ', '.join(f'{k} = ?' for k in row) + ' WHERE id = ?', (*row.values(), exists[0]))
        else:
            con.execute(f'INSERT INTO user ({", ".join(row)}) VALUES ({", ".join("?" * len(row))})', tuple(row.values()))
    con.commit()
    for r in con.execute('SELECT id, email, username, userType, plexId, permissions, avatar FROM user ORDER BY id'):
        print(r)
    con.close()


if __name__ == '__main__':
    main(sys.argv[1])
