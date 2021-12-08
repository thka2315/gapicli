from gapicli import apimodules, apimodule
import configparser
import sys
import os

sshkeyjson = """{
  "response": {
    "status": {
      "code": 404,
      "timestamp": "2021-12-05T12:52:22+01:00",
      "text": "Unknown function. Please specify function (ex: api.glesys.com/module/function",
      "transactionid": null
    },
    "module": {
      "description": "Module for managing SSH keys that can be used for GleSYS servers.",
      "authentication": {
        "required": "true",
        "apikey": "true",
        "user": {
          "username": "false",
          "cloudaccount": "true",
          "customernumber": "false"
        },
        "anonymous": "false"
      },
      "allowed_functions": [
        {
          "function": "add",
          "documentation": "Add public sshkey to your account which can be used when deploying new servers.",
          "post": true,
          "required_arguments": [
            "sshkey",
            "description"
          ]
        },
        {
          "function": "list",
          "documentation": "List your saved sshkeys.",
          "get": true,
          "post": true
        },
        {
          "function": "remove",
          "documentation": "Remove specified sshkey.",
          "post": true,
          "required_arguments": [
            "sshkeyids"
          ]
        }
      ]
    },
    "debug": {
      "input": []
    }
  }
}
"""

config = configparser.ConfigParser()
if os.path.exists('gapicli.conf'):
    config.read('gapicli.conf')
else:
    print("Configuration file was not found")
    sys.exit(0)
apiserver = config['main']['apiserver']
apiuser = config['main']['apiuser']
apikey = config['main']['apikey']

def test_apimodule():
    sshkey = apimodule('sshkey', sshkeyjson)
    assert sshkey.functions() == ['add','list', 'remove']
    assert sshkey.documentation('list') == 'List your saved sshkeys.'
    assert sshkey.requestdata(['list']) == ('/sshkey/list', {})
    assert sshkey.url(['list']) == '/sshkey/list'
    assert sshkey.functions() == ['add', 'list', 'remove']
    assert sshkey.required_arguments('add') == ['sshkey', 'description']
    assert sshkey.post_allowed('remove') == True
    assert sshkey.get_allowed('remove') == False
    assert sshkey._toboolean("true") == True
    assert sshkey.auth_required() == True
    assert sshkey.anonymous() == False
    assert sshkey.data(['add', 'description', 'test']) == {'description': 'test'}

def test_apimodules():
    api = apimodules(apiserver, apiuser, apikey)
    assert api.listfunctions() == ["account", "api", "archive", "country", "customer", "domain", "email", "filestorage", "invoice", "ip", "loadbalancer", "network", "networkadapter", "objectstorage", "paymentcard", "project", "server", "sshkey", "transaction", "user", "vpn"]
    assert api.suboptions('sshkey', 'a') == ['add ']
