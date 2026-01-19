echo "-- dns_challenge_clean.sh"

ls -lR /etc/letsencrypt > /certbot_shared/etc_letsencrypt.log
cp -Lr /etc/letsencrypt/live/$CERTBOT_DOMAIN /certbot_shared/.
chmod 777 /certbot_shared/$CERTBOT_DOMAIN

echo clean > /certbot_shared/CERTBOT_DOMAIN_CLEAN
