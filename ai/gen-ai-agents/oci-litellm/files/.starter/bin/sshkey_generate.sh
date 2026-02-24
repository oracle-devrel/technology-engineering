# Create a SSH KEY for the compute
# Stage: pre terraform
#
# Date : 2022_09_25: Test OK
# 
FILE=target/ssh_key_starter
if [ -f "$FILE" ]; then
    echo "$FILE exists."
else 
    mkdir -p target
    echo "Generating SSH KEY"
    ssh-keygen -b 2048 -t rsa -f $FILE -q -N ""
    chmod 600 $FILE*
    # echo "Uploading the ssh key to bucket xxx-terraform"
    # oci os object put --bucket-name=${TF_VAR_prefix}-terraform --force --file $FILE
    # oci os object put --bucket-name=${TF_VAR_prefix}-terraform --force --file $FILE.pub
fi
