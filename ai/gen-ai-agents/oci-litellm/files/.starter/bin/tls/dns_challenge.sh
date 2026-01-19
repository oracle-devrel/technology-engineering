echo "-- dns_challenge.sh"
echo $CERTBOT_DOMAIN > /certbot_shared/CERTBOT_DOMAIN
echo $CERTBOT_VALIDATION > /certbot_shared/CERTBOT_VALIDATION
env > /certbot_shared/dns_challenge_env.log

. /certbot_shared/dns_shared_function.sh

wait_file /certbot_shared/DNS_CREATED


