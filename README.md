# P4 Changelist Weblink Trigger


## Overview
* This trigger aims to scrape the changelist descriptions submitted to a perforce server and then attach them as weblinks to the corresponding assets in P4DAM. 

## Participants

* Ryan Maffesoli

## Installation
[Descript Video Explanation](https://share.descript.com/view/umz1rrArmF7)

* Currently, the running triggers via source doesn't require any additional installation beyond cloning the repository, having Python 3.9 or later, and installing the requirements

## Requirements
Python              3.9 or greater  
p4python            2023.2.2581979 or greater
requests            2.32.2   


## Environment File configuration

* Server configuration and access keys are defined in the environment.py file. You'll need to provide your Helix Dam web address as well as your HTH Internal Account Key to access the API with authentication.
```bash
os.environ["DAM_SERVER_ADDRESS"] = "http://ip_or_domain_name"
os.environ["DAM_ACCOUNT_KEY"] = "c531XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
os.environ["P4PORT"] = 'ssl:p4_server_address:1666'
os.environ["P4USER"] = 'user_name'

```

## Trigger Setup Example
* When adding these triggers to your system we recommend using the provided spawn_process wrapper function, This allows for the triggers to fire as detached subprocesses so that the User's submission experience isn't slowed down with each triggers processing.
```bash
	p4-cl-link change-commit //... "python3.9 /home/perforce/triggers/p4_cl_link/main.py %changelist%"
	
```


## Todo list
- [ ] Test Coverage
- [ ] Possibly simplify config setup to a json file
