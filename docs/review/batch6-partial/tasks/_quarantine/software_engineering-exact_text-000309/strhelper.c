/* strhelper.c - version 2.0.0 */
#include <string.h>

int my_strlen(const char *s) {
    int n = 0;
    while (*s++) n++;
    return n;
}

void my_strcpy(char *dst, const char *src) {
    while ((*dst++ = *src++));
}
