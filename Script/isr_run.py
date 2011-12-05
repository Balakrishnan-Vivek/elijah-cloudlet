#!/usr/bin/env python
import xdelta3
import os
import commands
import filecmp
import sys
import subprocess
import getopt
import time
import socket
from datetime import datetime, timedelta
import telnetlib
import pylzma
from flask import Flask,flash, request,render_template, Response,session,g
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Response
import re
import json

# global constant and variable
WEB_SERVER_PORT_NUMBER = 9095
ISR_ORIGIN_SRC_PATH = '/home/krha/Cloudlet/src/ISR/src'
ISR_ANDROID_SRC_PATH = '/home/krha/Cloudlet/src/ISR/src-mock'
user_name = ''
server_address = ''
launch_start = datetime.now()
launch_end = datetime.now()

# web server configuration
app = Flask(__name__)
app.config.from_object(__name__)

# web server for receiving command
@app.route("/isr", methods=['POST'])
def isr():
    global user_name
    global server_address

    print "Receive isr_info (run-type, application name) from client"
    json_data = request.form["isr_info"]
    metadata = json.loads(json_data)

    run_type = metadata['run-type'].lower()
    application_name = metadata['application'].lower()
    print "Client request : %s, %s --> connecting to %s with %s" % (run_type, application_name, server_address, user_name)
    
    if run_type in ("cloud", "mobile") and  application_name in ("moped", "face", "null"):
        # Run application
        if run_type == "cloud":
            print "Client request : %s, %s --> connecting to %s with %s" % (run_type, application_name, server_address, user_name)
            ret = do_cloud_isr(user_name, application_name, server_address)
        elif run_type == "mobile":
            print "Client request : %s, %s --> connecting to %s with %s" % (run_type, application_name, server_address, user_name)
            do_mobile_isr(user_name, application_name, server_address)
        
        if ret:
            print "SUCCESS"
            return "SUCCESS"

    ret_msg = "Wrong parameter " + run_type + ", " + application_name
    print ret_msg
    return ret_msg


def isr_temp():
    run_type = "cloud"
    application_name = "face"
    if run_type in ("cloud", "mobile") and  application_name in ("moped", "face", "null"):
        # Run application
        if run_type == "cloud":
            print "Client request : %s, %s --> connecting to %s with %s" % (run_type, application_name, server_address, user_name)
            ret = do_cloud_isr(user_name, application_name, server_address)
        elif run_type == "mobile":
            print "Client request : %s, %s --> connecting to %s with %s" % (run_type, application_name, server_address, user_name)
            do_mobile_isr(user_name, application_name, server_address)
        
        if ret:
            print "SUCCESS"


def recompile_isr(src_path):
    command_str = 'cd %s && sudo make && sudo make install' % (src_path)
    print command_str
    ret1, ret_string = commands.getstatusoutput(command_str)
    if ret1 != 0:
        raise "Cannot compile ISR"
    return True


# command Login
def login(user_name, server_address):
    command_str = 'isr auth -s ' + server_address + ' -u ' + user_name
    ret, ret_string = commands.getstatusoutput(command_str)

    if ret == 0:
        return True, ''
    return False, "Cannot connected to Server %s, %s" % (server_address, ret_string)


# remove all cache
def remove_cache(user_name, server_address, vm_name):
    # list cache
    command_str = 'isr lshoard -l -s ' + server_address + ' -u ' + user_name
    print command_str
    ret, ret_string = commands.getstatusoutput(command_str)
    if ret != 0:
        return False, "Cannot list up VM hoard"

    # find UUID, which has vm_name
    lines = ret_string.split('\n')
    uuid = None
    for index, line in enumerate(lines):
        if line.find(vm_name) != -1 and len(lines) > (index+1):
            uuid = lines[index+1].lstrip().split(" ")[0]

    if uuid == None:
        return True, ''
    
    # erase cache
    command_str = 'isr rmhoard ' + uuid + ' -s ' + server_address + ' -u ' + user_name
    print command_str
    ret, ret_string = commands.getstatusoutput(command_str)

    return True


# resume VM
def resume_vm(user_name, server_address, vm_name):
    time_start = datetime.now()
    time_end = datetime.now()
    time_transfer_start = datetime.now()
    time_transfer_end = datetime.now()
    time_decomp_mem_start = datetime.now()
    time_decomp_mem_end = datetime.now()
    time_kvm_start = datetime.now()
    time_kvm_end = datetime.now()

    command_str = 'isr resume ' + vm_name + ' -s ' + server_address + ' -u ' + user_name + ' -F'
    print command_str
    time_start = datetime.now()
    proc = subprocess.Popen(command_str, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    while True:
        time.sleep(0.1)
        output = proc.stdout.readline()
        if len(output.strip()) != 0 and output.find("[krha]") == -1:
            sys.stdout.write(output)

        # time stamping using log from isr_client
        # Not reliable but fast for simple test
        if output.strip().find("Fetching keyring") == 0:
            time_transfer_start = datetime.now()
        elif output.strip().find("Decrypting and uncompressing") == 0:
            time_transfer_end = datetime.now()
            time_decomp_mem_start = datetime.now()
        elif output.strip().find("Updating hoard cache") == 0:
            time_decomp_mem_end = datetime.now()
            time_kvm_start = datetime.now()
        elif output.strip().find("Launching") == 0:
            time_kvm_end = datetime.now()
            break;

    # if we wait for process to end, we cannot return to web client
    # ret = proc.wait()
    time_end = datetime.now()
    print "Return from Resume"
    print "[Total Time] : ", str(time_end-time_start)
    print '[Transfer Time(Memory)] : ', str(time_transfer_end-time_transfer_start)
    print '[Decompression Time] : ', str(time_decomp_mem_end-time_decomp_mem_start)
    print '[KVM Time] : ', str(time_kvm_end-time_kvm_start)


# stop VM
def stop_vm(user_name, server_address, vm_name):
    command_str = 'isr clean ' + vm_name + ' -s ' + server_address + ' -u ' + user_name
    print command_str
    proc = subprocess.Popen(command_str, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    proc.stdin.write('y\n')
    ret = proc.wait()

    return True

# Exit with error message
def exit_error(error_message):
    print 'Error, ', error_message
    sys.exit(1)

def do_cloud_isr(user_name, vm_name, server_address):
    # compile ISR again, because we have multiple version of ISR such as mock android
    # This is not good approach, but easy for simple test
    # I'll gonna erase this script after submission :(
    recompile_isr(ISR_ORIGIN_SRC_PATH)

    # step1. login
    ret, err = login(user_name, server_address)
    if not ret:
        return False

    # step2. remove all cache
    ret, err = remove_cache(user_name, server_address, vm_name)
    if not ret:
        return False

    # step3. resume VM, wait until finish (close window)
    start_time = datetime.now()
    resume_vm(user_name, server_address, vm_name)
    end_time = datetime.now()

    return True


def do_mobile_isr(user_name, vm_name, server_address):
    pass


def isr_clean_all(server_address, user_name):
    # kill all process that has 'isr'
    # I really hate do this :(
    command_str = 'ps aux | grep isr'
    ret1, ret_string = commands.getstatusoutput(command_str)
    for line in ret_string.split('\n'):
        if line.find('isr') != -1 and line.find('isr_run.py') == -1 and line.find('vi ') == -1:
            pid = re.search('[A-Za-z]+\s+(\d+).*', line).groups(0)[0]
            command_str = 'kill -9 ' + pid
            print 'kill /isr + \t', command_str
            commands.getoutput(command_str)

    vm_names = ("face", "moped", "null")
    for vm_name in vm_names:
        ret = stop_vm(user_name, server_address, vm_name)
        ret = remove_cache(user_name, server_address, vm_name)

def print_usage(program_name):
    print 'usage\t: %s [run|clean] [-u username] [-s server_address] ' % program_name
    print 'example\t: isr_run.py run -u cloudlet -s dagama.isr.cs.cmu.edu'


def main(argv):
    global user_name
    global server_address

    if len(argv) < 3:
        print_usage(os.path.basename(argv[0]))
        sys.exit(2)

    operation = argv[1].lower()
    if not operation in ("clean", "run"):
        print "No supporing operation : ", operation
        print_usage(os.path.basename(argv[0]))
        sys.exit(2)

    try:
        optlist, args = getopt.getopt(argv[2:], 'hu:s:', ["help", "user", "server"])
    except getopt.GetoptError, err:
        print str(err)
        print_usage(os.path.basename(argv[0]))
        sys.exit(2)

    # required input variables
    user_name = None
    server_address = None

    # parse argument
    for o, a in optlist:
        if o in ("-h", "--help"):
            print_usage(os.path.basename(argv[0]))
            sys.exit(0)
        elif o in ("-u", "--user"):
            user_name = a
        elif o in ("-s", "--server"):
            server_address = a
        else:
            assert False, "unhandled option"

    if user_name == None or server_address == None:
        print_usage(os.path.basename(argv[0]))
        sys.exit(2)

    if operation == "clean":
        isr_clean_all(server_address, user_name)
        sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
    #isr_temp()
    app.run(host='0.0.0.0', port=WEB_SERVER_PORT_NUMBER, processes = 10)
