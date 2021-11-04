#!/bin/bash
# -------------------------------------------------------------------------
# This script is to upload the Jenkins log onto S3 bucket
#
# Parameters:
#   $1 - A path where the python virtual environment is located. 
#        The lftool is installed in this virtual environment
#   $2 - The S3 bucket
#   $3 - The S3 path to deploy the log onto
#   $4 - The url of the Jenkins build
#   $5 - The workspace of the Jenkins build
#
# History:
#   2021/10/27, Alisa created.
#--------------------------------------------------------------------------
python_venv=$1
s3_bucket=$2
s3_path=$3
build_url=$4
workspace=$5
# Enter the python virtual environment where lftool is installed
source $python_venv/bin/activate
# The default locale value will cause the deployment fail,
# so add the following code to change the value.
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
locale
# Deploy the log to S3 bucket
lftools deploy s3 "$s3_bucket" "$s3_path" "$build_url" "$workspace"
deactivate