# Setup

1. Resolve the project repository internally as
   `multicloud-control-plane/<repository>` before every operation. Read its
   `origin` only to confirm it is the expected handed-off private
   `nonprod-<project>` or `prod-<project>` repository whose default branch is
   `main`; never infer an organization from it. The matching
   `environments/<environment>/environment_information.md` supplies the
   approved handoff references.
2. Use `multicloud-control-plane/gitops-templates` at `main`. Choose
   `resources-catalog` for infrastructure or `operations-catalog` for OCI
   lifecycle work. The catalog is the only source for supported fields and
   destination paths. Platform CI and the selected orchestrator are the only
   validation authorities; do not recreate their checks locally.
3. A template-only `.github/CODEOWNERS.template` is valid; Project Team owns
   its active CODEOWNERS configuration.
4. A runtime-token manifest needs the repository secret
   `GITOPS_SECRET_VALUES_<ENVIRONMENT>` for its eventual workflow to succeed.
   Use `GITOPS_SECRET_VALUES_DEV`
   for `dev`, `GITOPS_SECRET_VALUES_TEST` for `test`,
   `GITOPS_SECRET_VALUES_UAT` for `uat`, and `GITOPS_SECRET_VALUES_PROD` for
   `prod`. Its value is a JSON object. Each OCI ADB administrator-password
   token is unique to that database. Build its secret member from the selected
   environment and the database mapping key: uppercase it, replace every run
   of non-alphanumeric characters with one underscore, then trim leading and
   trailing underscores. For database key `project45-adb1` in `dev`, commit
   the token `__DEV_PROJECT45_ADB1_ADMIN_PASSWORD__`; its JSON member is
   `DEV_PROJECT45_ADB1_ADMIN_PASSWORD`. For two ADBs, the required bundle
   therefore has two distinct members:

   ```json
   {
     "DEV_PROJECT45_ADB1_ADMIN_PASSWORD":"<set-the-first-ADB-admin-password>",
     "DEV_PROJECT45_ADB2_ADMIN_PASSWORD":"<set-the-second-ADB-admin-password>"
   }
   ```

   The key omits the surrounding double underscores. Render the catalog's
   generic ADB password placeholder separately for every database using that
   formula; reject a candidate that reuses one ADB password token. Before
   asking for confirmation, inspect the candidate's runtime-secret tokens and
   state its required bundle and every required member key in the preview.
   If the bundle does not exist, give a full copy-paste-safe JSON object whose
   only placeholders are secret values, and state that the administrator must
   replace those angle-bracket placeholders before saving it. If it already
   exists, give only the missing member-key fragment and instruct the
   administrator to add it to the existing JSON through the approved secret
   process, preserving every existing member. The agent cannot read or
   reconstruct those existing values. For an OCI ADB administrator password,
   also state the published runtime policy: 12 to 30 characters, at least one
   uppercase letter, lowercase letter, and digit, with no double quote and no
   `admin` substring in any casing. An agent cannot determine whether that
   bundle exists or whether its values meet that policy, so it must not imply
   that it has checked them. Never request, read, print, or set a secret value.
