#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>

/*
 * MAIN FUNCTION
 */
int main(int argc, char *argv[]) {
    int i = 0;
    while(1) {
      sleep(1);
      printf("%i\n", ++i);
    }
    return EXIT_SUCCESS;
}
