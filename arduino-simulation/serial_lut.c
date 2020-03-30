#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <termios.h>
#include <unistd.h>
#include <fcntl.h>

#define SPEED B115200
#define RBUF_SZ 50
#define WBUF_SZ 50
#define LUT_SZ 601

/* global vars */
int fd;

enum {
	NONE,
	SERIAL,
	INIT,
	WINDOW,
	RENDER,
	TEXTURE,
	FINAL
};

void cdie(const char *msg,int stage)
{
	puts(msg);
	switch(stage){
		case FINAL:
		case SERIAL:
			close(fd);
		default:
			exit(EXIT_SUCCESS);
	}
}

float flow[]= {
#include "flow.txt"
};

float pressure[]= {
#include "pressure.txt"
};

float volume[]= {
#include "volume.txt"
};

int
main(int argc, char **argv)
{
	(void)argc;
	(void)argv;
	char rbuf[RBUF_SZ];
	char *pbuf=malloc(200*sizeof(char));
	struct termios config;
	int s;

	if (argc!=2)
		cdie("please specify a serial port",NONE);

	/* posix terminal boilerplate */
	fd=open(argv[1], O_RDWR | O_NOCTTY | O_NDELAY);
	if(fd == -1) {
		  cdie("failed to open port",NONE);
	}
	if(!isatty(fd))
		cdie("port is not a tty",SERIAL);

	if(tcgetattr(fd, &config) < 0)
		cdie("failed to get config",SERIAL);

	config.c_iflag &= ~(IGNBRK | BRKINT | ICRNL |
				                     INLCR | PARMRK | INPCK | ISTRIP | IXON);
	config.c_oflag &= ~(OCRNL | ONLCR | ONLRET |
			                        ONOCR | OFILL | OLCUC | OPOST);
	config.c_lflag &= ~(ECHO | ECHONL | ICANON | IEXTEN | ISIG);

	config.c_cflag &= ~(CSIZE | PARENB);
   config.c_cflag |= CS8;
	config.c_cc[VMIN]  = 1;
	config.c_cc[VTIME] = 0;

	if(cfsetispeed(&config, SPEED) < 0 || cfsetospeed(&config, SPEED) < 0) 
		cdie("failed to set serial port speed",SERIAL);
   
	if(tcsetattr(fd, TCSAFLUSH, &config) < 0) 
		cdie("failed to configure serial port",SERIAL);
	/* end posix terminal boilerplate */
		
   /* pbuf is the parse buffer pbufi its idex variable,
	* wbuf is the write buffer
	* ws is the size of the written string 
	* rfl is the read float
	* idx is the index for the lookup table*/

	int pbufi,i,ws,idx;
	pbufi=0;
	char wbuf[WBUF_SZ];
	for(;;){
		s=read(fd,rbuf,sizeof(char)*RBUF_SZ);
		if(s>0) {
			for (i=0;i<s;i++){
				pbuf[pbufi]=rbuf[i];
				pbufi=(pbufi==199)?0:pbufi+1;
				if(rbuf[i]=='\r'){
					pbuf[pbufi]=0;
					idx= (int) atof(pbuf)*20;
					if (idx > LUT_SZ-1 ) idx=0;
					ws=snprintf(wbuf,WBUF_SZ,"%f %f %f \r\n",flow[idx],pressure[idx],volume[idx]);
					write(fd,wbuf,ws*sizeof(char));
					pbufi=0;
				}
			}
		}
	}
	free(pbuf);
	cdie("exit",FINAL);
}

