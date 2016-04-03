#include <stdio.h>
#include <string.h>

void vuln_func(char *buffer)
{
    char local_buffer[10];
    strcpy(local_buffer, buffer);
}

int main(int argc, char *argv[])
{
    char str[1024];
    gets(str);

    if(strlen(str) > 100) {
        while(1);
    }

    vuln_func(str);
    return 0;
}
