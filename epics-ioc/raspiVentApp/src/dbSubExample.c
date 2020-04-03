#include <stdio.h>

#include <aSubRecord.h>
#include <dbDefs.h>
#include <epicsExport.h>
#include <registryFunction.h>
#include <subRecord.h>

#include <math.h>

const float flow[][] = {
#include "flow.txt"
};


int mySubDebug;

static long mySubInit(subRecord *precord) {
  if (mySubDebug)
    printf("Record %s called mySubInit(%p)\n", precord->name, (void *)precord);
  return 0;
}

static long mySubProcess(subRecord *precord) {
  int idx;
  int idy;
  if (mySubDebug)
    printf("Record %s called mySubProcess(%p)\n", precord->name,
           (void *)precord);
  idx = floor(20 * precord->a);
  idx = (idx < 0)? 0: idx; // Check LUT limits 
  idx = (idx > 199)? 199: idx;
  idy = floor(20 * precord->b);
  idy = (idy < 0)? 0: idx; // Check LUT limits 
  idy = (idy > 199)? 199: idx;
  precord->val = flow[idx][idy];
  // precord->val++;
  return 0;
}

static long myAsubInit(aSubRecord *precord) {
  if (mySubDebug)
    printf("Record %s called myAsubInit(%p)\n", precord->name, (void *)precord);
  return 0;
}

static long myAsubProcess(aSubRecord *precord) {
  if (mySubDebug)
    printf("Record %s called myAsubProcess(%p)\n", precord->name,
           (void *)precord);
  return 0;
}

/* Register these symbols for use by IOC code: */

epicsExportAddress(int, mySubDebug);
epicsRegisterFunction(mySubInit);
epicsRegisterFunction(mySubProcess);
epicsRegisterFunction(myAsubInit);
epicsRegisterFunction(myAsubProcess);
