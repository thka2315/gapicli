#!/usr/bin/python3

# G API command line interface
# Copyright 2020 Thomas Karlsson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# thomas.karlsson@relea.se

import requests
import os
import sys
import json
import argparse
import shlex
import urllib.parse
import xml.etree.ElementTree as ET
import configparser
from typing import List, Any, Union, Dict, Tuple, Optional
import readline


class apimodule:
    """
        Arguments
            modulename: The name of the module
            modulejson: The JSON string from
            curl -H "Accept: application/json" https://api.glesys.com/sshkey
    """
    def __init__(self, modulename: str, modulejson: str):
        self.modulename = modulename
        self.json = modulejson
        self.moduledata = json.loads(self.json)
        # print(self.moduledata)

    def _toboolean(self, indata: Union[bool, str]) -> bool:
        """
            Converts a string with 'true' to a real True, or False
            Arguments
                indata: string with true
            Returns
                Boolean
        """
        if isinstance(indata, str):
            if indata == 'true':
                return True
            else:
                return False
        if isinstance(indata, bool):
            return indata

    def module(self) -> Dict[str, Any]:
        """
            Returns a dict with module data
        """
        if 'module' not in self.moduledata['response']:
            return dict()

        return self.moduledata['response']['module']

    def function(self, item: str) -> Dict[str, Any]:
        """
            Arguments:
                item: Which function to return, if it exists
            Return:
                Dict with the function
        """
        for oneitem in self.module()['allowed_functions']:
            if oneitem['function'] == item:
                return oneitem

        return dict()

    def functions(self) -> List[str]:
        """
            Return:
                A list with all functions
                (https://api.glesys.com/api/listfunctions)
        """
        functionlist: List[str] = list()
        for item in self.module()['allowed_functions']:
            functionlist.append(item['function'])

        return functionlist

    def documentation(self, item: str) -> str:
        """
            Arguments:
                item: Which function to get the documentation for
            Returns:
                A string with the functions documentation
        """
        if item not in self.functions():
            return str()

        function = self.function(item)

        return function['documentation']

    def required_arguments(self, item) -> List[str]:
        """
            Arguments:
                item: Which function to list required arguments
            Returns
                A list with required arguments
        """
        if item not in self.functions():
            return list()
        function = self.function(item)
        if 'required_arguments' not in function:
            return list()

        return function['required_arguments']

    def optional_arguments(self, item) -> List[str]:
        """
            Arguments:
                item: Which function to list optional arguments
            Returns
                A list with optional arguments
        """
        if item not in self.functions():
            return list()
        function = self.function(item)
        if 'optional_arguments' not in function:
            return list()

        return function['optional_arguments']

    def post_allowed(self, item) -> bool:
        """
            Arguments:
                item: Which function to check for
            Returns
                True or False if POST is allowed
        """
        if item not in self.functions():
            return False

        function = self.function(item)
        if 'post' in function and function['post']:
            return True

        return False

    def get_allowed(self, item) -> bool:
        """
            Arguments:
                item: Which function to check for
            Returns
                True or False if GET is allowed
        """
        if item not in self.functions():
            return False

        function = self.function(item)
        if 'get' in function and function['get']:
            return True

        return False

    def authentication(self) -> Dict[str, Any]:
        """
            Returns:
                Authentication dict
        """
        if 'authentication' not in self.module():
            return dict()

        return self.module()['authentication']

    def username(self) -> str:
        """
            Returns
                The used username
        """
        authobject = self.authentication()
        if 'user' not in authobject:
            return str()

        if 'username' not in authobject['user']:
            return str()

        return authobject['user']['username']

    def cloudaccount(self) -> str:
        """
            Returns
                The used cloudaccount
        """
        authobject = self.authentication()
        if 'user' not in authobject:
            return str()

        if 'cloudaccount' not in authobject['user']:
            return str()

        return authobject['user']['cloudaccount']

    def customernumber(self) -> str:
        """
            Returns
                The used customernumber
        """
        authobject = self.authentication()
        if 'user' not in authobject:
            return str()

        if 'customernumber' not in authobject['user']:
            return str()

        return authobject['user']['customernumber']

    def auth_required(self) -> bool:
        """
            Returns
                True if authentication is required to use this module
        """
        authobject = self.authentication()
        if 'required' not in authobject:
            return False

        return self._toboolean(authobject['required'])

    def allowed_with_apikey(self) -> bool:
        """
            Returns
                True if authentication is allowed with apikey
        """
        authobject = self.authentication()
        if 'apikey' not in authobject:
            return False

        return self._toboolean(authobject['apikey'])

    def anonymous(self) -> bool:
        """
            Returns
                True if anonymous use is allowed
        """
        authobject = self.authentication()
        if 'anonymous' not in authobject:
            return False

        return self._toboolean(authobject['anonymous'])

    def data(self, modulecommands: List[str]) -> Dict[str, str]:
        """
            Arguments:
                modulecommands: The commands except the first
            Returns:
                A dict with all parameters
            Example:
                {'sshkey': 'xxxxxxx', 'description': 'mykey'}
        """
        postdata: Dict[str, str] = dict()
        currentarg = str()
        currentfunction = str()
        functionexists = False
        for cli in modulecommands:
            if cli in self.functions():
                functionexists = True
                currentfunction = cli
                continue
            if cli in self.required_arguments(currentfunction):
                currentarg = cli
                postdata[currentarg] = ''
                continue
            if cli in self.optional_arguments(currentfunction):
                currentarg = cli
                postdata[currentarg] = ''
                continue
            if functionexists:
                if cli.startswith('{') or cli.startswith('['):
                    userdict = json.loads(cli)
                else:
                    userdict = cli
                postdata[currentarg] = userdict

        return postdata

    def url(self, functioncommands: List[str]) -> str:
        for cli in functioncommands:
            if cli in self.functions():
                return '/' + os.path.join(self.modulename, cli)

        return '/' + self.modulename

    def requestdata(self, functioncommands: List[str]) -> Tuple[str, Union[Dict[str, str], None]]:
        """
            Arguments:
                functioncommands: [functions]
            Example:
                ['add', 'description', 'my_key']
            Returns:
                /sshkey/add and a dict with arguments
        """
        if self.post_allowed(functioncommands[0]):
            retdata = self.data(functioncommands)
            return self.url(functioncommands), retdata
        if self.get_allowed(functioncommands[0]):
            ret = self.url(functioncommands)
            return ret, None

        return '/', None


class apimodules:
    def __init__(self, apiserver: str, apiuser: str, apikey: str):
        self.apiserver = apiserver
        self.apiuser = apiuser
        self.apikey = apikey
        self.modulesjson = json.loads(self.apicall_get('api/listfunctions/'))

    def apicall_get(self, function: str, acceptjson: bool = True) -> str:
        url = urllib.parse.urljoin(self.apiserver, function)
        auth = requests.auth.HTTPBasicAuth(self.apiuser, self.apikey)
        if acceptjson:
            headers = {'Accept': 'application/json'}
        else:
            headers = {'Accept': 'application/xml'}
        request = requests.get(url=url, timeout=(5, 14), auth=auth,
                               headers=headers)

        return request.content.decode()

    def apicall_post(self, function: str, body: Dict[str, Any],
                     acceptjson: bool = False) -> str:
        url = urllib.parse.urljoin(self.apiserver, function)
        auth = requests.auth.HTTPBasicAuth(self.apiuser, self.apikey)
        if acceptjson:
            headers = {'Accept': 'application/json'}
        else:
            headers = {'Accept': 'application/xml'}
        request = requests.post(url=url, timeout=(5, 14), auth=auth,
                                json=body, headers=headers)

        return request.content.decode()

    def module(self, modulename: str) -> apimodule:
        """
            HTTP GET to https://api.glesys.com/[modulename]/

            Arguments:
                modulename which module to ask for
            Returns:
                xml data for that module
        """
        jsondata: str = str()
        if os.path.exists(modulename + '.json'):
            jsondata = self.readfile(modulename + '.json')
        else:
            jsondata = self.apicall_get(modulename)
            with open(modulename + '.json', 'w') as jsonfile:
                jsonfile.write(jsondata)

        return apimodule(modulename, jsondata)

    def readfile(self, path: str) -> str:
        with open(path, 'r') as jsonfile:
            return jsonfile.read()

        return str()

    def listmodules(self) -> List[str]:
        modules = list(self.modulesjson['response']['modules'].keys())
        # modules.append('help')

        return modules

    def suboptions(self, modulename: str, text: str) -> List[str]:
        if modulename in self.listmodules():
            current = self.module(modulename)
            subresult = [x + ' ' for x in current.functions() if x.startswith(text)]
            return subresult

        return current.functions()

    def subrequired(self, modulename: str, suboption: str, text: str) -> List[str]:
        if suboption in self.module(modulename).functions():
            current = self.module(modulename)
            subresult = [x + ' ' for x in current.required_arguments(suboption) if x.startswith(text)]
            options = [x + ' ' for x in current.optional_arguments(suboption) if x.startswith(text)]
            return subresult + options

        return current.required_arguments(suboption)

    def complete(self, text: str, state: int) -> Union[str, None]:
        try:
            tokens = readline.get_line_buffer().split()
            commands = self.listmodules()
            results = [x + ' ' for x in commands if x.startswith(text)] + [None]
            if len(tokens) > 0:
                if len(tokens) == 1:
                    if tokens[0] in commands:
                        results = self.suboptions(tokens[0], text) + [None]
                if len(tokens) == 2:
                    if tokens[0] in commands:
                        results = self.suboptions(tokens[0], text) + [None]
                    subfuncs = [x + ' ' for x in self.module(tokens[0]).functions()]
                    if tokens[1] in self.module(tokens[0]).functions() and text == '':
                        results = self.subrequired(tokens[0], tokens[1], text) + [None]
                if len(tokens) > 2:
                    results = self.subrequired(tokens[0], tokens[1], text) + [None]

            return results[state]
        except Exception as e:
            print(e)

        return str()


def main():
    parser = argparse.ArgumentParser(description='G API explorer')
    parser.add_argument('commands',
                    nargs='*',
                    type=str,
                    help='Commands to execute instead of interactive'
                    )
    args = parser.parse_args()
    config = configparser.ConfigParser()
    if os.path.exists('gapicli.conf'):
        config.read('gapicli.conf')
    else:
        print("Configuration file was not found")
        sys.exit(0)
    apiserver = config['main']['apiserver']
    apiuser = config['main']['apiuser']
    apikey = config['main']['apikey']
    readline.parse_and_bind("tab: complete")
    api = apimodules(apiserver, apiuser, apikey)

    cmds = list()
    if args.commands == list():
        readline.set_completer(api.complete)
        try:
            line = input("{}@{}> ".format(apiuser, apiserver))
            cmds = shlex.split(line)
        except KeyboardInterrupt:
            pass
    else:
        cmds = args.commands

    if not cmds:
        sys.exit(0)
    module = api.module(cmds[0])
    del(cmds[0])
    remoteurl, data = module.requestdata(cmds)
    if data is None:
        print(api.apicall_get(remoteurl, json = True))
    else:
        print(api.apicall_post(remoteurl, data, acceptjson = True))

    if os.path.exists(module.modulename + '.json'):
        os.remove(module.modulename + '.json')

if __name__ == '__main__':
    main()
