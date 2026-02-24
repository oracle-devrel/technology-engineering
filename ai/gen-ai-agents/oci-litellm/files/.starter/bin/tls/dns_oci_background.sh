#!/usr/bin/env bash

# Wait that Certbot create the validation token
. $BIN_DIR/tls/dns_shared_function.sh
. $BIN_DIR/shared_bash_function.sh

wait_file $TARGET_DIR/certbot_shared/CERTBOT_DOMAIN ]

export CERBOT_DOMAIN=`cat $TARGET_DIR/certbot_shared/CERTBOT_DOMAIN`
export CERTBOT_VALIDATION=`cat $TARGET_DIR/certbot_shared/CERTBOT_VALIDATION`
export TF_VAR_dns_acme_challenge=_acme-challenge.${CERBOT_DOMAIN}
export TF_VAR_dns_data=$CERTBOT_VALIDATION
oci dns record rrset update --force --zone-name-or-id $TF_VAR_dns_zone_name --domain $TF_VAR_dns_acme_challenge --rtype 'TXT' --items '[{"domain":"'$TF_VAR_dns_acme_challenge'", "rdata":"'$TF_VAR_dns_data'", "rtype":"TXT","ttl":300}]' 
exit_on_error "DNS-01 Create DNS Challenge Record"
# XXX Check that DNS is really propagated ? 
sleep 10
echo "done" > $TARGET_DIR/certbot_shared/DNS_CREATED

# Wait that Certbot create the validation token
wait_file $TARGET_DIR/certbot_shared/CERTBOT_DOMAIN_CLEAN ]
oci dns record rrset delete --force --zone-name-or-id $TF_VAR_dns_zone_name --domain $TF_VAR_dns_acme_challenge --rtype 'TXT' 
exit_on_error "DNS-01 Delete DNS Challenge Record"
