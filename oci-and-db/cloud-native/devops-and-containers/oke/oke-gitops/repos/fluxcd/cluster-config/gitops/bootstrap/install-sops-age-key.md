# Generate age key for the cluster

1. Install age: https://github.com/FiloSottile/age?tab=readme-ov-file#installation
2. Run:
```shell
  age-keygen -o age.key
  kubectl -n flux-system create secret generic sops-age --from-file=age.agekey=age.key
```
3. Remember to reference it in the Flux resources, see this for global decryption: https://fluxoperator.dev/docs/crd/kustomization/#controller-global-decryption
4. Share the public age key to the developers

# Use the age public key to encrypt secrets
Install SOPS: https://github.com/getsops/sops/releases

To encrypt a file:
`sops encrypt <file> --in-place`

To encrypt a Secret:
`sops encrypt <file> --encrypted-regex '^(data|stringData)$'`