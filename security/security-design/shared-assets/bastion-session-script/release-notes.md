# Release Notes

## Feb 20, 2024 Release Notes - v1.0.3

- Fixed an issue where sometimes the bastion session resource was used before it was fully ready.

## Jul 4, 2023 Release Notes - v1.0.2

- Documentation and textual improvements.

## Nov 24, 2022 Release Notes - v1.0.1

- Added option to specify an existing private and public SSH key pair instead of using a generated temporary SSH key pair.

## Nov 1, 2022 Release Notes - v1.0.0

- Simplified determining the ssh command by retrieving it from the OCI Bastion Session info.
- Improved OCI Bastion Session creation including improved failure detection.
- Final first release.

## Sep 8, 2022 Release Notes - Beta 0.9.2

- When using CygWin (e.g. via MobaXTerm) on Windows, ssh-keygen key location and access work slightly differently. Added detection for this.
- Improved verbose output to include ssh commands.
- Removed obsolete oci lookup command.

## Sep 6, 2022 Release Notes - Beta 0.9.1

- Added support for specifying the SSH key type and key length.
- Improved error message for when bastion or resource lookup by name fails, it takes a few minutes to work on OCI after new creations.

## Sep 2, 2022 Release Notes - Beta 0.9.0

- Added CTRL-C handling in the script to keep doing cleanup activities where required.
- Adopted many bash code quality improvements based on static code analysis by shellcheck.
