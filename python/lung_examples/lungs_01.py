from scipy import signal as sig
import numpy as np
import matplotlib.pyplot as plt

tbs=1e-3 #time between samples in [s]

#Transfer function
num = [1, 420, 0]
den = [1, 620, 4000]
tf = sig.lti(num, den)

#signal
time=np.arange(0,10,tbs)
Pao=np.sin(time*6)+2
Pao=np.array([0]*3000+[1]*3000+[0]*4000)

time=np.array(range(15))+1
Pao=np.array([1,1,1,2,2,3,4,4,5,6,6,5,2,1,1])

time_out, Q, xout=tf.output(Pao,time)
time_step, step=tf.step()
Q
plt.plot(time,Pao)
plt.plot(time,Q)
plt.plot(time,xout)
plt.plot(time,np.cumsum(Q))
plt.plot(time_step,step)
plt.pause(10000)
