export TF_VAR_dns_name=$1
echo TF_VAR_dns_name=$TF_VAR_dns_name 
certbot -d $TF_VAR_dns_name --agree-tos --register-unsafely-without-email --manual --preferred-challenges dns \
        --manual-auth-hook /certbot_shared/dns_challenge.sh \
        --disable-hook-validation --force-renewal certonly

ls -lR /etc/letsencrypt > /certbot_shared/etc_letsencrypt.log

# Copy the certificate to the shared directory 
cp -Lr /etc/letsencrypt/live/$TF_VAR_dns_name /certbot_shared/.
chmod -R 777 /certbot_shared/$TF_VAR_dns_name

# Request OCI to clean the OCI DNS entry
echo clean > /certbot_shared/CERTBOT_DOMAIN_CLEAN