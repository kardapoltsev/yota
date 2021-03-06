#!/usr/bin/env python3 
# PYTHON_ARGCOMPLETE_OK

# Copyright 2013 Alexey Kardapoltsev
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import urllib
from urllib import request
import http.cookiejar
import re
import json
import sys
import os

_tariffs = list("{}".format(x) for x in range(250, 901, 50))

def _get_home_dir():
    if os.name != "posix":
        from win32com.shell import shellcon, shell
        return shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
    else:
        return os.path.expanduser("~")

_config_file = os.path.join(_get_home_dir(), ".yotarc")



def change_offer(args):
    (login, password) = _get_credentials(args)
    (device, cj) = _login(login, password)
    _change(args.speed, device, cj)

def _get_credentials(args):
    login = None
    password = None
    try:
        with open(_config_file, "r") as conf_file:
            conf = json.load(conf_file)
            login = conf["login"]
            password = conf["password"]
    except IOError:
        login = args.login
        password = args.password
        pass

    if login == None and password == None:
        print('Please specify username and password or create a file ' + _config_file + ' with credentials like {"login": "your_login", "password": "your_password"}')
        sys.exit(0)

    return login, password



def _parse_device(page):
    print("parsing slider")
    slider = _parse_slider(page)
    product = list(slider)[0]
    return slider[product]


def _parse_slider(page):
    page = page.split("\n")

    for line in page:
        match = re.search(".*var sliderData =(.*);", line)
        if match:
            return json.loads(match.group(1))

    unavailable = "Личный кабинет временно недоступен"
    for line in page:
        match = re.search(".*{}.*".format(unavailable), line)
        if match:
            print(unavailable)
            sys.exit(0)

    print("slider data not found in page")
    sys.exit(0)


import pprint
def _change(speed, device, cj):
    print("changing offer")
    #pprint.pprint(device)
    offer = next(x for x in device["steps"] if x["amountNumber"] == speed)
    #pprint.pprint(offer)
    remain = offer["remainNumber"] + " " + offer["remainString"]
    productId = device["productId"]

    url = "https://my.yota.ru/selfcare/devices/changeOffer"
    values = {
          "product" : productId,
          "offerCode" : offer["code"],
          "areOffersAvailable" : "false",
          "period" : remain,
          "status" : device["status"],
          "autoprolong" : "1",
          "isSlot" : "false",
          "resourceId" : "",
          "currentDevice" : "0",
          "username" : ""
          }


    data = urllib.parse.urlencode(values)
    data = data.encode('utf-8')
    opener = request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    response = opener.open(url, data)
    currentProduct = device["currentProduct"]
    print("Changing plan from {} {} to {} {}".format(currentProduct["amountNumber"], currentProduct["amountString"], offer["amountNumber"], offer["amountString"]))
    print("Time remaining: {}".format(remain))


def _login(login, password):
    print("authorizing")
    url = "https://login.yota.ru/UI/Login"
    values = {"IDToken1" : login,
          "IDToken2" : password,
          "goto" : "https://my.yota.ru:443/selfcare/loginSuccess",
          "gotoOnFail" : "https://my.yota.ru:443/selfcare/loginError",
          "org" : "customer" }

    data = urllib.parse.urlencode(values)
    data = data.encode('utf-8')

    cj = http.cookiejar.CookieJar()
    opener = request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    response = opener.open(url, data)

    #page = opener.open("https://my.yota.ru/devices").read().decode("utf-8")
    page = response.read().decode("utf-8")
    device = _parse_device(page)
    return (device, cj)


topParser = argparse.ArgumentParser()

topParser.add_argument("speed", help = "speed to set", choices=_tariffs)
topParser.add_argument("-u", "--user", dest="login", help = "your username")
topParser.add_argument("-p", "--password", dest="password", help = "your password")

topParser.set_defaults(func = change_offer)

try:
    import argcomplete
    argcomplete.autocomplete(topParser)
except ImportError:
    print("try install python argcomplete")
    pass

args = topParser.parse_args()

args.func(args)
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
