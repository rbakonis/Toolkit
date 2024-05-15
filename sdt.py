#!/bin/python
# -*- coding: utf-8 -*-

# Schedule downtime with Logic Monitor
# Compatible with Python 2 & 3
# Run with -h for help.
# Update the access_id, access_key, and url in the Generate_Request function

import argparse
import sys
import json
import logging
import requests
import json
import hashlib
import base64
import time
import hmac
import platform
import time
from collections import OrderedDict

def Render_Splash():
    print("█░░ █▀█ █▀▀ █ █▀▀ █▀▄▀█ █▀█ █▄░█ █ ▀█▀ █▀█ █▀█")
    print("█▄▄ █▄█ █▄█ █ █▄▄ █░▀░█ █▄█ █░▀█ █ ░█░ █▄█ █▀▄")
    print("----------------------DOWNTIME SCHEDULER------")

def Render_Menu(items):

    for k,v in items.items():
        print(k + ": " + v)

    selection = str(input("Select an option from the list above: "))
    while selection not in items.keys():
        print("Invalid selection. Try again")
        selection = input("Select an option from the list above: ")

    return selection

def Generate_Request(method, path, request_data='', params=''):
    access_id = ''
    access_key = ''

    #Construct URL
    url = 'https://<organization_name>.logicmonitor.com/santaba/rest' + path

    #Get current time in milliseconds
    epoch = str(int(time.time() * 1000))

    #Concatenate Request details
    request_vars = method + epoch + request_data + path

    #Construct signature
    hmac1 = hmac.new(access_key.encode(),msg=request_vars.encode(),digestmod=hashlib.sha256).hexdigest()
    signature = base64.b64encode(hmac1.encode())

    #Construct headers
    auth = 'LMv1 ' + access_id + ':' + signature.decode() + ':' + epoch
    headers = {'Content-Type':'application/json','Authorization':auth}

    #Make request

    response = requests.request(method, url= url+params, data=request_data, headers=headers)

    #Print status and body of response
    if response.status_code >= 200 and response.status_code <= 206:
        logging.debug(response.json())
        #print(response.text)
        return response.json()
    else:
        print(response.text)
        logging.error(response.text)
        return False
    

def check_resource(resource):
    device_list = Generate_Request(method="GET", path="/device/devices", params="?filter=name~" + resource + "*")
    if device_list:
        if device_list['data']['total'] == 1:
            return device_list['data']['items'][0]['name']
    else:
        return False


def main(args):

    # Match the device name with a resource in Logic Monitor
    device_name =  check_resource(args.Resource)
    
    if not device_name:
        print("Unable to locate " + args.Resource + " in Logic Monitor. Exiting.")
        sys.exit(1)


    # Assume start time is now
    start_time = int(time.time())

    # Logic Monitor wants epoch times in miliseconds
    start_date_time = start_time * 1000
    
    # Define payload
    data = {
            'type': "DeviceSDT",
            'sdtType' : 1,
            'comment' : '',
            'startDateTime' : start_date_time,
            'endDateTime' : '',
            'deviceDisplayName' : device_name
    }

    if args.Duration:
        data['endDateTime'] = (start_time + (3600 * args.Duration)) *  1000
    else:
        Render_Splash()

        # Present downtime options to user:
        options = OrderedDict()
        options['1'] = '15 Minutes'
        options['2'] = '30 Minutes'
        options['3'] = '1 Hour'
        options['4'] = '8 Hours'
        options['5'] = '24 Hours'
        options['6'] = '3 Days'
        options['7'] = '1 Week'

        # Get selection
        selection = Render_Menu(options)

        if selection == '1':
            data['endDateTime'] = (start_time + 900) * 1000

        elif selection == '2':
            data['endDateTime'] = (start_time + 1800) * 1000

        elif selection == '3':
            data['endDateTime'] = (start_time + 3600) * 1000

        elif selection == '4':
            data['endDateTime'] = (start_time + 28800) * 1000

        elif selection == '5':
            data['endDateTime'] = (start_time + 86400) * 1000

        elif selection == '6':
            data['endDateTime'] = (start_time + 259200) * 1000

        elif selection == '7':
            data['endDateTime'] = (start_time + 604800) * 1000
    
    
    # Add a comment
    if args.Comment:
        data['comment'] = args.Comment
    else:
        try:
            comment = str(input("Enter a comment to associate with this downtime: "))
        except:
            comment = "No comment"
        
        data['comment'] = comment


    # Schedule downtime and confirm result
    result = Generate_Request(method="POST", path="/sdt/sdts", request_data=json.dumps(data))
    if result:
        if 'status' in result:
            if result['status'] == 200:
                print('SDT scheduled successfully')
        elif 'errmsg' in result:
            print("Failed to schedule downtime. Error:" + result['errmsg'])
        else:
            print('Failed to schedule downtime. Unknown error. Response:' + result)
    else:
        print('Failed to schedule downtime. Unknown error.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--Resource", nargs='?', default=platform.node(), help ="Name of the resource to place in scheduled downtime")
    parser.add_argument("-d", "--Duration", nargs='?', help="Scheduled downtime duration in hours", type=int)
    parser.add_argument("-c", "--Comment", help="A comment to associate with the scheduled downtime")
    args = parser.parse_args()
    main(args)