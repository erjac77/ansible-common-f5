# F5 COMMON UTILITY MODULE FOR ANSIBLE

This repository provides utility classes and helper functions to ease the interaction between Ansible and the following F5 systems:

* BIG-IP ([ansible-module-f5bigip](https://github.com/erjac77/ansible-module-f5bigip))
* BIG-IQ
* iWorkflow

## REQUIREMENTS

* Ansible >= 2.4.0 (ansible)
* DeepDiff >= 3.3.0 (deepdiff)
* F5 Python SDK >= 3.0.14 (f5-sdk)
* Python-Future >= 0.16.0 (future)
* Requests >= 2.18.4 (requests)
* Six >= 1.11.0 (six)

## INSTALLATION

```shell
sudo pip install git+git://github.com/erjac77/ansible-common-f5.git#egg=ansible-common-f5
```

## LICENSE

Apache 2.0

## AUTHOR INFORMATION

* Eric Jacob ([@erjac77](https://github.com/erjac77))

### CONTRIBUTORS

* Gabriel Fortin ([@GabrielFortin](https://github.com/GabrielFortin))
