# F5 COMMON UTILITY MODULE FOR ANSIBLE

This repository provides utility classes and helper functions to ease the interaction between Ansible and F5 systems.

* BIG-IP
* BIG-IQ
* iWorkflow

## REQUIREMENTS

* Ansible >= 2.2.0 (ansible)
* F5 Python SDK >= 2.2.2 (f5-sdk)

## INSTALLATION

Example using Virtualenv:

```
# Install pip
sudo apt-get install python-pip

# Install virtualenv
sudo pip install virtualenv

# Make a virtual environment for your Ansible installation and activate it
mkdir ansible
cd ansible
virtualenv venv
source ./venv/bin/activate

# Install the F5 Common Utility Module for Ansible and all its dependencies (ansible, f5-sdk, etc.)
pip install git+git://github.com/erjac77/ansible-common-f5.git#egg=ansible-common-f5
```

## LICENSE

Apache 2.0

## AUTHOR INFORMATION

Eric Jacob ([@erjac77](https://github.com/erjac77))