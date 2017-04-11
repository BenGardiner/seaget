#!/usr/bin/python2
#Dumps the memory of a seagate hd using the jumper pin serial interface
import serial
import sys,os,re,argparse
import time
from wgetstyle import *

debug=0
#automagicly set to 115200 baud
fast=0
#1 is slow 0 is fastest 0.1 is the sweetspot
timeout=0.01
benchmark=1
writing=0

try:
    device=sys.argv[1]
    dumpfile=sys.argv[2]
    baud=sys.argv[3]
    start_addr=int(sys.argv[4], 0)
    end_addr=int(sys.argv[5], 0)

    memf=open(dumpfile,'w')
except:
    print 'Usage:'
    print sys.argv[0]+' device dumpfile baud start_addr end_addr\n'
    print 'Default baud should be 38400 maximum is 115200\n'
    quit()

def send(ser,command):
    ser.write(command+"\n")
    inco=""
    modus=""
    while 1:
        try:
            arr=ser.readline()
            if arr!="":
                inco=inco+arr
            else:
                if debug>=2:
                    print inco
                modus=re.findall('F3 (.)>',inco)
                break
                #print 'Next command'
        except:
            print 'Exception! (in send)'
            if writing==1:
                memf.close()
            break
    return inco,modus

def get_modus(ser):
    inco,modus=send(ser,"")
    return modus[0]

def set_baud(ser,baud):
    modus=get_modus(ser)
    print 'Setting baud to '+str(baud)
    if modus!="T":
        print 'Changing mode to T'
        send(ser,"/T")
    send(ser,"B"+str(baud))
    ser = serial.Serial(port=device, baudrate=baud, bytesize=8,parity='N',stopbits=1,timeout=timeout)
    send(ser,"/"+modus)
    return ser

def init(device,baud,fast=fast):
    ser = serial.Serial(port=device, baudrate=baud, bytesize=8,parity='N',stopbits=1,timeout=timeout)
    #Initialize the command line
#    print ser.inWaiting()
#    print dir(ser)
#    if send(ser,"\n")[1]==[]:
#        print 'Got no modus bad'
#        quit()
#    print send(ser,"\n")[1]
    print send(ser,"\x1A")[1]
    if baud=="38400" and fast==1:
        baud=115200
        try:
            set_baud(ser,baud)
            ser = serial.Serial(port=device, baudrate=baud, bytesize=8,parity='N',stopbits=1,timeout=timeout)
        except:
            print 'You probably already are on 11500 baud'
    send(ser,"/1")
    return ser

def parse(buff):
    hex=""
    fooR=re.compile(r'.+ = (..)')
    parsed=fooR.findall(buff)
    for line in parsed:
        hex=hex+re.sub(' ','',line)
    bin=hex.decode("hex")
    return hex,bin

def display_buffer(ser,num):
    #num xxxx
    foo,bar=send(ser,'B'+str(num))
    return parse(foo)

def display_memory(ser, addr):
    if debug>=1:
        print '+'+format(addr, 'x')+" - "
    foo,bar=send(ser,'+'+format(addr, 'x'))
    parsed=parse(foo)
    return parsed

def dump_memory(ser,dumpfile, start_addr, end_addr):
    writing=1
    k=0
    total=(end_addr - start_addr)/1024.0
    stime=time.time() #start time
    print 'Starting memory dump'
    addr = start_addr
    while addr < end_addr:
        k=k+1
        zz=time.time()
        retries=0
        while retries < 5:
            parsed=display_memory(ser,addr)
            if len(parsed[1])!=1:
                print 'Got the wrong size!!!!!! %d of %s' % (len(parsed[1]), parsed[1])
                retries = retries + 1
                continue
            else:
                break
        if len(parsed[1])!=1:
            print 'FATAL unable to read'
            sys.exit(1)

        mem=parsed[1]
        addr = addr + 1
        if benchmark==1:
            size=k/1024.0
            speed=round(512/(time.time()-zz),2)
            percentage=round(100.0/total*size,2)
            minleft=round((time.time()-stime)/k*(247*128-k)/60,2)
            if debug==0:
                progress_bar(time.time()-stime,size*1024,total*1024)
            elif debug>0:
                print 'time:'+str(time.time()-stime)
                print 'size:'+str(size)
                print 'total:'+str(total)
        memf.write(mem)
    memf.close()
    writing=0

ser=init(device,baud)
#print send(ser,'')
#print display_buffer(ser,00)[0]
try:
    modus=get_modus(ser)
except:
    print "Couldn't even get the modus - quitting"
    if debug<2:
        print 'Try it using debug=2'
    quit()
if modus!="1":
     print 'Somethings not right here'
     quit()
dump_memory(ser,dumpfile,start_addr,end_addr)

print 
