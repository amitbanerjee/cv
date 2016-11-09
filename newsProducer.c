#include<stdio.h>
#include<string.h>
#include<sys/socket.h>
#include<arpa/inet.h>
#include<unistd.h>

#define PORT 8080
#define BUFF_SIZE 1024
 
int main(int argc , char *argv[])
{
    int socket_desc , client_sock , c , read_size;
    struct sockaddr_in server , client;
    char client_message[BUFF_SIZE];
    char news[BUFF_SIZE];
     
    //Create socket
    socket_desc = socket(AF_INET , SOCK_STREAM , 0);
    if (socket_desc == -1)
    {
        printf("Could not create socket\n");
        return 1;
    }
    printf("Socket created\n");
     
    //Prepare the sockaddr_in structure
    server.sin_family = AF_INET;
    server.sin_addr.s_addr = INADDR_ANY;
    server.sin_port = htons( PORT );
     
    //Bind
    if( bind(socket_desc,(struct sockaddr *)&server , sizeof(server)) < 0)
    {
        //print the error message
        printf("bind failed. Error\n");
        return 1;
    }
    printf("bind done\n");
     
    //Listen
    listen(socket_desc , 3);
     
    //Accept and incoming connection
    printf("Waiting for incoming connections...\n");
    c = sizeof(struct sockaddr_in);
     
    memset(client_message, '\0', BUFF_SIZE);
    //accept connection from an incoming client
    client_sock = accept(socket_desc, (struct sockaddr *)&client, (socklen_t*)&c);
    if (client_sock < 0)
    {
        printf("accept failed\n");
        return 1;
    }
    printf("Connection accepted\n");
     
    //Receive a message from client
    while( (read_size = recv(client_sock , client_message , BUFF_SIZE , 0)) > 0 )
    {
	if (strncmp(client_message, "send", 4) == 0){
	  //Generate new news
          memset(news, '\0', BUFF_SIZE);
          sprintf(news, "NEWS: %d\n", random()%10000);
          printf("Generated a new news - %s", news);
          //Send the message back to client
          write(client_sock , news , BUFF_SIZE);
	}
       else {
         printf("Meaningless request from Portal: %s\n", client_message);
       }
       memset(client_message, '\0', BUFF_SIZE);
    }
     
    if(read_size == 0)
    {
        printf("Client disconnected\n");
        fflush(stdout);
    }
    else if(read_size == -1)
    {
        printf("recv failed\n");
    }
     
    return 0;
}
