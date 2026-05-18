#!/usr/bin/env bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR

. ./env.sh

# https://yum.oracle.com/oracle-linux-python.html

sudo dnf install -y python3.12 python3.12-pip python3-devel
# sudo pip3.12 install pip --upgrade
sudo update-alternatives --set python /usr/bin/python3.12
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install virtual env python_env
uv venv myenv
source myenv/bin/activate
uv pip install -r requirements.txt

# Prima
sudo dnf module enable -y nodejs:20
sudo dnf install -y nodejs
# LiteLLM bug
python -m prisma generate --schema myenv/lib64/python3.12/site-packages/litellm/proxy/schema.prisma

# Postgres (LiteLLM config)
sudo dnf install -y @postgresql
sudo /usr/bin/postgresql-setup --initdb
sudo systemctl enable postgresql
sudo sed -i "s/ident/md5/g" /var/lib/pgsql/data/pg_hba.conf
sudo systemctl restart postgresql

# . ./env.sh
# echo $DATABASE_URL
# sudo su - postgres
# psql 
# \l

cd /tmp
sudo -u postgres psql -c "CREATE USER litellm_user WITH ENCRYPTED PASSWORD '$TF_VAR_db_password';"
sudo -u postgres psql -c "ALTER USER litellm_user WITH PASSWORD '$TF_VAR_db_password';"
sudo -u postgres psql -c "CREATE DATABASE litellm_db OWNER litellm_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE litellm_db TO litellm_user;"
cd -

# Config.yaml
sed -i "s/##TF_VAR_compartment_ocid##/$TF_VAR_compartment_ocid/" config.yaml
sed -i "s/##TF_VAR_region##/$TF_VAR_region/" config.yaml
sed -i "s/##TF_VAR_current_user_ocid##/$TF_VAR_current_user_ocid/" config.yaml
sed -i "s/##TF_VAR_tenancy_ocid##/$TF_VAR_tenancy_ocid/" config.yaml

# Patch DAC/Cohere
cp myenv/lib64/python3.12/site-packages/litellm/llms/oci/chat/transformation.py myenv/lib64/python3.12/site-packages/litellm/llms/oci/chat/transformation.py.backup
cp oci_litellm/transformation.py myenv/lib64/python3.12/site-packages/litellm/llms/oci/chat/transformation.py