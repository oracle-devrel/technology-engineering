# Bundled NSSM (the Non-Sucking Service Manager) v2.24

`win64/nssm.exe` is bundled so the installer never depends on `nssm.cc` (which
has repeatedly returned HTTP 503). NSSM is **public domain** — see https://nssm.cc/.
`Install-NSSM` in `Install-OCI-Prometheus.ps1` uses this binary if present and only
falls back to downloading when it is absent.
