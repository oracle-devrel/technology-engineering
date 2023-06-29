#!/bin/bash
# Version: @(#).parameter1.sh 1.0.0 
# License
# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License (UPL), Version 1.0.
# See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/folder-structure/LICENSE) for more details.
#
#@  Set needed parameter 
#@
#
# Update history:
#
# V 1.0.0 28.06.2023 initial version
#



# ---------------------------------------------------------------------------------------------------------------------------------------------
# CUSTOMER SPECIFIC VALUES - please update appropriate
# ---------------------------------------------------------------------------------------------------------------------------------------------
export COMPARTMENT_OCID=<your_compartment>																				# Compartment Name: 
export REGION_PROFILE=FRANKFURT																							# oci region profile e.g. frankfurt
export CREATE_BLOCK_VOLUME=0																							# create Block volume 0=no // 1=yes
export CREATE_BLOCK_VOLUME_BACKUP=0																						# create Block volume backup 0=no // 1=yes

# ---------------------------------------------------------------------------------------------------------------------------------------------
# SECURITY SPECIFIC VALUES - please update appropriate
# ---------------------------------------------------------------------------------------------------------------------------------------------
export AD=<your_ad_number>																								#
export AD_PREFIX=<your_prefix>																							# Prifix of Availability Domain
export FRANKFURT_REGION_IDENTIFIER=<your_region_identifier>																# 
export FRANKFURT_BLOCK_VOLUME_NAME=BlockVolumeFrankfurt																	#
export FRANKFURT_AVAILABILITY_DOMAIN="${AD_PREFIX}:${FRANKFURT_REGION_IDENTIFIER}-AD-${AD}"								# [AD Prefix]:[Region Identifier]-AD-[Number of Availability Domain] see https://docs.oracle.com/en-us/iaas/Content/General/Concepts/regions.htm
export VAULT_OCID=<your_vault_ocid>																						# Vault OCID
export MasterEncryptionKey_OCID=<your_masterencryptionkey_ocid>															# MasterEncryptionKey OCID

# ---------------------------------------------------------------------------------------------------------------------------------------------
# VALUES (normally do not touch)
# ---------------------------------------------------------------------------------------------------------------------------------------------
export LOG_FILE=<your_log_file_name_including_the_path>                            										# 
export DEBUG_LEVEL=0                                                													# 0 (off); 1 (low); 2 (high)
export PF1=###																											# Prefix 1 - used to introduce function
export PF2="${PF1}.###:"																								# Prefix 2 - used to log informations inside functions
export MYcolor="${IYellow}"                                         													# define output color
if [ ${DEBUG_LEVEL} -eq 0 ] ; then export MYcolor=$ICyan   ; fi
if [ ${DEBUG_LEVEL} -eq 1 ] ; then export MYcolor=$IPurple ; fi
if [ ${DEBUG_LEVEL} -eq 2 ] ; then export MYcolor=$IRed    ; fi
# ---------------------------------------------------------------------------------------------------------------------------------------------
# end of file
# ---------------------------------------------------------------------------------------------------------------------------------------------
