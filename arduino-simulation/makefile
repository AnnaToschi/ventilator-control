W_FLAGS    = -Wall -Wextra -std=c99 -pedantic

CFLAGS     = $(W_FLAGS) -g 
LFLAGS     = $(W_FLAGS) 

CC =  gcc
RM = /bin/rm

TARGET = serial_lut
CFILES := $(wildcard *.c)
OBJECT := $(patsubst %.c, %.o, ${CFILES})
HEADER := $(wildcard *.h)

all: comp link 

link: $(TARGET)

comp: $(OBJECT) 

%.o: %.c $(HEADER)
	$(CC) $(CFLAGS) -c $<

$(TARGET): $(OBJECT)
	$(CC) $(LFLAGS) $(D_LIBS) -o $@ $^ $(S_LIBS)

edit:
	vim makefile

count:
	wc -l *.c

clean:
	$(RM) -f *~ *.o $(TARGET) 
