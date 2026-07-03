/* netio.c - version 1.0.0 */
#include <stdio.h>
#include <string.h>

int send_data(const char *buf, int len) {
    /* v1: validate length */
    if (len <= 0) return -1;
    return len;
}

int recv_data(char *buf, int maxlen) {
    if (maxlen <= 0) return -1;
    return 0;
}
