"""Operator-only immediate session revocation; no cloud calls."""
import argparse
import json
import os
import sqlite3
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--subject',required=True,help='Verified OIDC subject to sign out')
args=parser.parse_args()
with sqlite3.connect(Path(os.getenv('DATA_DIR','/data'))/'assistant.sqlite3') as db:
    ids=[row[0] for row in db.execute('SELECT id,user FROM sessions') if json.loads(row[1])['sub']==args.subject]
    db.executemany('DELETE FROM sessions WHERE id=?',[(v,) for v in ids])
print(f'Revoked {len(ids)} sessions. Already-running jobs require separate operator review.')
