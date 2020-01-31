# Ansible Playbooks
Inventory of playbooks and examples used to manage the day to day operational tasks of installing and configuring DataStax Enterprise software suite using package install method.

At end of this exercise, we would have installed the following,
* DSE `6.7.6` cluster with two datacenters
* A 2-node DC1 with _C*_ only workload; A 2-node DC2 with _C* + Analytics_ workload
* OpsCenter `6.7.6` with an active-passive setup (i.e. 2 VMs in total for running OpsCenter daemon)
* A 2-node DSE `6.7.6` cluster dedicated for storing OpsCenter collection metrics data of the monitored cluster
* Agents installed on all the DSE nodes
* This playbook covers installation of DSE softwares both `online` and `offline` where, `online` refers to servers having
internet connectivity and `offline` for servers without internet connectivity

**_Note_**: This could be customized to deploy _N_-number of DCs with _N_-number of nodes with varying workloads.

## Assumptions
* This playbook was built and tested using a supported version of Ansible [v2.8.3](https://docs.ansible.com/ansible/latest/reference_appendices/release_and_maintenance.html#release-status) at the time of this writing.
* In future, if updating Ansible version, thoroughly test the playbooks to ensure there is backward compatiblity.
* Only `Package Installation` is currently tested & supported at the moment although there are some code related to `Tarball Installation` in this playbooks which could be used in future for customizations.
* There are variety of ways to manage the layout of the Ansible roles & playbooks as per the user's need/requirement and this whole setup could be customized accordingly.
* Environment provisioning is not covered by this Ansible scripts

## Provisioned Infrastructure Expectations
* All the required virtual machines are available as per the sizing for the required workload,
* All provisioned virtual machines are pre-applied with [DataStax Recommended Settings](https://docs.datastax.com/en/dse/6.7/dse-admin/datastax_enterprise/config/configRecommendedSettings.html),
* All required [DataStax Enterprise](https://docs.datastax.com/en/security/6.7/security/secFirewallPorts.html) and [OpsCenter](https://docs.datastax.com/en/opscenter/6.7/opsc/reference/opscLcmPorts.html) ports are opened between the virtual machines accordingly,
* An Ansible control machine / node is provisioned per the [requirements](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#control-node-requirements)

## DataStax softwares installation using package install method
This is a playbook to build the DSE environment on the infrastructure created and provisioned. The IP addresses are placed into named groups and the the playbook assumes a RHEL 7.6 Maipo image. The playbook should be executed from the users designated Ansible control machine / host. The password / private key to gain access to the hosts will be provided as part of the pre-requisite steps for creating the infrastructure.

This particular playbook has the following defined roles:
* `os-settings`: create users, groups and configure any kernel settings.
* `standard-packages`: install any packages required.
* `store-prep`: Download DSE and Agents for the OpsCenter cluster
* `db-prep`: Download DSE and Agents for the OpsCenter cluster
* `store-configure`: Configure parameters and correct DSE version
* `db-configure`: Configure parameters and correct DSE version
* `opscenter-prep`: Download OpsCenter
* `opscenter-configure`: Configure OpsCenter parameters and correct version.
* `rolling-restart`: Perform a conditional rolling restart.

Execute the playbook using the following to add any pre-tasks:
```
ansible-playbook -u <username> --ask-pass --ask-become-pass -i inventory/hosts pre-tasks.yml

# Optionally use `-v` at the end of the command to run it in verbose mode (or) run it with `--check` option for a trial run (or) use `--syntax-check` to test syntax.
```

The aim of the playbook is to automate the OS configuration, deployment of all DataStax software and configuration.

It may be easier to stored the specific user configurations in different branches i.e. diffent branches for Dev, Pre-prod, Production etc.,

### Directory Layout
As of the initial delivery, [the default file locations for the package installation](https://docs.datastax.com/en/install/6.7/install/dsePackageLoc.html) is followed which could be customized and updated accordingly.

## Deployment Process

### Do some pre-requisites for the Ansible control center / host
Based on the Linux environment, use either `apt` (or) `yum` to install required dependencies.
```
sudo apt-get install software-properties-common
sudo apt-add-repository -y ppa:ansible/ansible
sudo apt-get update
sudo apt-get install -y ansible
sudo apt-get install -y git

(or)

sudo yum install -y ansible-2.8.3
```
One could also download RPM package and install it. **Reference**: [How to install or upgrade an RPM package in RHEL?](https://access.redhat.com/solutions/1189)

Tweak [Ansible configuration file](https://docs.ansible.com/ansible/latest/reference_appendices/config.html#ansible-configuration-settings-locations) file, `ansible.cfg`
```
forks=50
host_key_checking = False
```

### Setup Inventory
Use hosts file in the repo as an example and configure `/etc/ansible/hosts` (or) hosts file in user's custom location appropriately.

### Deploy DSE, OpsCenter and Agents. Also, configure automatic failover setup for OpsCenter
```
ansible-playbook -u <username> --ask-pass --ask-become-pass -i inventory/hosts build-site.yml

# Optionally use `-v` at the end of the command to run it in verbose mode (or) run it with `--check` option for a trial run (or) use `--syntax-check` to test syntax.
```

### Perform a DSE patch upgrade. For e.g. upgrade from `6.7.6` to `6.7.7` version
```
ansible-playbook -u <username> --ask-pass --ask-become-pass -i inventory/hosts patch-version-upgrade.yml --extra-vars "worker_jobs_killed=<y_or_n> dse_patch_version=<6.7.latest>"

# Optionally use `-v` at the end of the command to run it in verbose mode (or) run it with `--check` option for a trial run (or) use `--syntax-check` to test syntax.
```

### Start the metrics and multi-datacenter `OnionDSEDev` cluster
```
ansible-playbook -i inventory/host rolling-restart.yml
```

## Key files to configure
Below are key files that one would need to update, per environment prior to running the Ansible playbooks to install & configure DSE softwares.

### `inventory/hosts` file
This is the file where we will be placing the public/private IPs of the VMs.

The layout will be as follows,
```
[opscenter]
<format: IP_address failover_role=[active|passive] in its own line>
<there can be at most only 2 rows here. 1st row will be active OpsCenter IP with `failover_role=active` and 2nd row will be passive OpsCenter IP with `failover_role=passive`>

[storeseeds]
<format: IP_address rack=<rack_name> in its own line>

[storenonseeds]
<format: IP_address rack=<rack_name> in its own line>

[store:children]
storeseeds
storenonseeds

[clusterseeds]
<format: IP address in its own line>

[cluster:children]
<format: Name of the sub-group in its own line. For e.g. DC1>
<format: Name of the sub-group in its own line. For e.g. DC2>

[DC1]
<format: IP address rack=<rack_name> in its own line>

[DC2]
<format: IP address rack=<rack_name> in its own line>
```

An example layout is below,
```
[opscenter]
40.124.26.172 failover_role=active
13.85.60.218 failover_role=passive

[storeseeds]
157.54.201.233 rack=rack1

[storenonseeds]
23.98.278.165 rack=rack2

[store:children]
storeseeds
storenonseeds

[clusterseeds]
40.44.239.9
40.84.139.112

[cluster:children]
DC1
DC2

[DC1]
40.87.239.9 rack=rack1
40.84.393.57 rack=rack2

[DC2]
102.214.117.55 rack=rack1
401.84.199.112 rack=rack2
```

### `group_vars/[all|DC1|DC2|store]/vars.yaml` file
Update the detail in these files accordingly. If one doesn't have a separate DSE cluster to store OpsCenter metrics collection data, set `metrics_cluster` to `false` at `all/vars.yaml` file.

# Disclaimer
Any Ansible code shared is distributed on an _"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND_, either expressed or implied. Users will need to be maintaining it going forward based on their custom needs.
