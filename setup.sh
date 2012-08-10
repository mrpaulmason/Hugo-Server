#!/bin/bash

rm -rf ~/.ec2
mkdir -p ~/.ec2
cp -rf security/hugo.pem ~/.ec2
cp bash_profile ~/.bash_profile

#touch ~/.ssh/authorized_keys
#if [ "`grep ec2-keypair ~/.ssh/authorized_keys`" == "" ]; then
#   echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDYEVzyNdqTBRE9jsj3d+/U8v22dYx7qYPt3Ww0mvv+/fIT+EFb7CWukVcUUufdCcmFtOZ4xdIjsEkbPKKlhjKic9StGlK8VPBBEMjXOa+wd1L8JsNhnBaaftKKsjtTRLS8/UU9CGMoLeClKpRECBEHw/6X9eMFRrOtQ8hMCMjCHswfcGEMZNWDgVD0jsUy4GVYyfDh/PB85pBJWbapn1YfXFEiluPhEu0nGsPXExtafKqKaZEtPag7qMG+skkp5rNfOMrqHct3fAlsCbCj02QD/+gE/EGt7vrDo6ihkTIeSSkaPOV2mTF8sTm6qfplX9pNouXpps3wdHPifGoFQZJ9 ec2-keypair" >> ~/.ssh/authorized_keys
#fi

ssh-add ~/.ec2/hugo.pem
