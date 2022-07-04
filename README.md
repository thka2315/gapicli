# This project has moved to https://gitlab.com/thka/

# G API Command line interface
This is an interactive shell for using API
Just start it and use TAB for completion

## Example
Show servers

    gapicli.py server list

    gapicli.py
    xxxxxxx@https://api.glesys.com> server [TAB]
    allowedarguments     edit                 reboot
    backup               estimatedcost        reset
    clone                limits               resetlimit
    console              list                 resetpassword
    costs                listbackups          resourceusage
    create               listiso              start
    createfrombackup     mountiso             status
    destroy              networkadapters      stop
    details              previewcloudconfig   templates
    xxxxxxx@https://api.glesys.com> server

    user@localhost:~$ gapicli.py server list | jq .

Create server

    xxxxxxx@https://api.glesys.com> server create templatename debian-11 datacenter Falkenberg hostname testserver disksize 5 memorysize 512 cpucores 1 platform KVM users '[{"username":"cloud", "password":"password"}]'

Delete server

    xxxxxxx@https://api.glesys.com> server destroy serverid <serverid> keepip false
