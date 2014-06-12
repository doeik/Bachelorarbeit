#include <stdlib.h>
#include <stdio.h>

/*
 * MAIN FUNCTION
 */
int main(int argc, char *argv[]) {
    int *p;
    while(1) {
      p = malloc(sizeof(int));
      if (p != NULL) {
	 *p = 10000;
      }
    }
}
