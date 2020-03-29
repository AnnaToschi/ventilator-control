#Author:    Andre Torres
#date:      29.03.2020

import sys
import serial
from time import sleep
from scipy import signal as sig
import numpy as np
import matplotlib.pyplot as plt

def printHelp(a):
    pass

#Transfer function
num = [1, 420, 0]
den = [1, 620, 4000]
tf = sig.lti(num, den)
t_vec=[]
Pao_vec=[]

#plot preparation
plt.ion()
fig1=plt.figure(1)
# draw and show it
fig1.canvas.draw()
plt.show(block=False)

def do_plot(time, Pao, Q):
    plt.figure(1)
    plt.plot(time,Pao,'ko')
    plt.plot(time,Q,'ro')
    plt.draw()
    plt.pause(0.0001)

def do_model(time, Pao):
    t_vec.append(time)
    Pao_vec.append(Pao)
    if len(t_vec)< 4:
        time_out, Q, xout=tf.output(Pao_vec,t_vec)
    else:
        time_out, Q, xout=tf.output(Pao_vec[-4:],t_vec[-4:])
        print(Pao_vec[-4:])
    return Q

def compute(time, Pao):
    Q=do_model(time,Pao)
    try:
        if len(Q) >1:
            QQ=Q[-1]
    except:
        QQ=Q
    print("Q=",QQ)
    do_plot(time,Pao,QQ)



if __name__ == "__main__":

    #DEFINE STATES
    #0 - waiting value
    #1 - computing
    if len(sys.argv) > 1:
        port=sys.argv[1]


    state   = 0
    run     = True

    baud  = 115200
    try:
        with serial.Serial(port, baud) as com:
            while run:
                if state == 0:          #if waiting command
                    try:
                        print('trying')
                        input_val = com.readline()
                        input_val = input_val.decode()
                        print('not here')
                        print(input_val)
                        state += 1
                    except EOFError:    #end of file reached
                        print("")       #clear line
                        run=False
                    except KeyboardInterrupt:    #CTR+C
                        print("")       #clear line
                        run = False     #terminate
                elif state == 1:        #if ready to send command
                    if input_val=="":
                        state=0
                    else:
                        a=input_val.split(" ")
                        time=int(a[0])
                        Pao=int(a[1])
                        #print("GOT ", time, Pao)
                        compute(time,Pao)
                        sleep(1)
                        state=0
    except Exception as e:
        print(e)
        exit(-1)

    while True:
        pass

    #exit(0)
    #except Exception as e:
    ##    print(e)
    #    exit(-1)
