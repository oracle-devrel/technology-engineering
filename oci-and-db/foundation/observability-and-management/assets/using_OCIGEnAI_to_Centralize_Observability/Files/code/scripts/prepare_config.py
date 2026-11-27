"""Create private operator configuration without contacting any cloud service."""
from pathlib import Path
import os
import secrets
from cryptography.fernet import Fernet


def main():
    root = Path(__file__).resolve().parent.parent
    copies = {
        root / '.env': root / '.env.example',
        root / 'config/access.json': root / 'config/access.example.json',
        root / 'config/mcp.json': root / 'config/mcp.example.json',
        root / 'config/models.json': root / 'config/models.example.json',
        root / 'secrets/config': root / 'config/oci.example',
    }
    if any(path.exists() for path in copies):
        raise SystemExit('Existing configuration found; no files changed. Review and edit it manually.')
    os.umask(0o077)
    (root / 'secrets').mkdir(mode=0o700, exist_ok=True)
    for destination, template in copies.items():
        text = template.read_text()
        if destination.name == '.env':
            text = text.replace('SESSION_SECRET=REPLACE_WITH_AT_LEAST_32_RANDOM_CHARACTERS',
                                'SESSION_SECRET=' + secrets.token_urlsafe(48))
            text = text.replace('CONNECTION_ENCRYPTION_KEY=\n',
                                'CONNECTION_ENCRYPTION_KEY=' + Fernet.generate_key().decode() + '\n')
        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'w') as stream:
            stream.write(text)
    print('Created private working configuration and fresh local secrets. Replace the remaining example values privately.')


if __name__ == '__main__':
    main()
