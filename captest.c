#include <stdlib.h>
#include <stdio.h>
#include <sys/capability.h>

int main() {
  cap_t proc_capset;
  cap_flag_value_t flag;
  proc_capset = cap_get_proc();
  int cap;
  for (cap = 0; cap <= CAP_LAST_CAP; cap++) {
    cap_value_t currentcap = cap;
    char* capname;
    cap_get_flag(proc_capset, currentcap, CAP_EFFECTIVE, &flag);
    capname = cap_to_name(currentcap);
    printf("%s: %d\n", capname, flag);
  }
  return 0;
}