# HLL_CRCON_Discord_watch_killrate

A plugin for HLL CRCON (see : https://github.com/MarechJ/hll_rcon_tool) that watches and report players who get "too much" kills per minute.

![image](https://github.com/user-attachments/assets/9733fc2c-e50b-43c8-89d8-404098563f45)

Install (open this file for complete procedure) :
- Create a `custom_tools` folder in CRCON's root (`/root/hll_rcon_tool/`) ;
- Copy `watch_killrate.py` in `/root/hll_rcon_tool/custom_tools/` ;
- Copy `custom_common.py` in `/root/hll_rcon_tool/custom_tools/` ;
- Copy `custom_translations.py` in `/root/hll_rcon_tool/custom_tools/` ;
- Copy `restart.sh` in CRCON's root (`/root/hll_rcon_tool/`) ;
- Edit `/root/hll_rcon_tool/config/supervisord.conf` to add this bot section : 
  ```conf
  [program:watch_killrate]
  command=python -m custom_tools.watch_killrate
  environment=LOGGING_FILENAME=watch_killrate_%(ENV_SERVER_NUMBER)s.log
  startretries=100
  startsecs=120
  autostart=true
  autorestart=true
  ```

Config :
- Edit `/root/hll_rcon_tool/custom_tools/watch_killrate.py` and set the parameters to your needs ;
- Restart CRCON :
  ```shell
  cd /root/hll_rcon_tool
  sh ./restart.sh
  ```
Any change to these files :
- `/root/hll_rcon_tool/custom_tools/watch_killrate.py` ;
- `/root/hll_rcon_tool/custom_tools/custom_common.py` ;
- `/root/hll_rcon_tool/custom_tools/custom_translations.py` ;  
...will need a CRCON restart (using `restart.sh` script) to be taken in account.
