#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdbool.h>
#include<string.h>
#include<sys/socket.h>
#include<arpa/inet.h>

#define NUM_READERS 5
#define MAX_NEWS_SIZE 1024
#define PRODUCER_IP "127.0.0.1"
#define PORT 8080

typedef struct {
    pthread_mutex_t mutex; 	  // needed to add/remove data from the shared_news
    pthread_cond_t cond_portal;   // Used to notify Portal when all news are read
    pthread_cond_t cond_readers;  // Used to notify readers when new news arrives
    char news_buf[MAX_NEWS_SIZE]; // Place for readers to consume news
    bool read[NUM_READERS];       // Readers not yet read news
} news_t;

typedef struct {
    int       thread_num;       /* Application-defined thread # */
    news_t    *shared_news;      /* From command-line argument */
} thread_info;

// Portal thread
void* portal(void *arg) {
    news_t *shared_news = (news_t*)arg;
    int i;
    bool allread;
    int sock;
    struct sockaddr_in server;
    char message[MAX_NEWS_SIZE] , server_reply[MAX_NEWS_SIZE];

    printf("Production Thread Started.\n");
    //Create socket
    sock = socket(AF_INET , SOCK_STREAM , 0);
    if (sock == -1)
    {
        printf("Could not create socket");
        exit(1);
    }
    printf("Socket created\n");
     
    //server.sin_addr.s_addr = inet_addr(PRODUCER_IP);
    server.sin_addr.s_addr = inet_addr(PRODUCER_IP);
    server.sin_family = AF_INET;
    server.sin_port = htons( PORT );
 
    //Connect to remote server
    if (connect(sock , (struct sockaddr *)&server , sizeof(server)) < 0)
    {
        printf("connect failed. Error\n");
        exit(1);
    }
     
    printf("Connected\n");

    while(1) {

        pthread_mutex_lock(&shared_news->mutex);

	allread = true;
	for (i=0; i<NUM_READERS; i++) { 
          if (shared_news->read[i] == false) {
            allread = false;
            break;
	  }
        }

        if(allread == false) { // Some readers have not read yet
            // wait until some elements are consumed
            pthread_cond_wait(&shared_news->cond_portal, &shared_news->mutex);
        }

	//Get data from news producer
	memset(message, '\0', MAX_NEWS_SIZE);
	sprintf(message, "send");
	if( send(sock , message , strlen(message) , 0) < 0)
        {
            printf("Send failed. Error\n");
            exit(1);
        }

	memset(server_reply, '\0', MAX_NEWS_SIZE);
        if( recv(sock , server_reply , MAX_NEWS_SIZE , 0) < 0)
        {
            printf("recv failed. Error.\n");
            exit(1);
        }
         
        printf("Portal received a new news - %s",server_reply);
	strcpy(shared_news->news_buf, server_reply);
         
        // append data to the shared_news
	for (i=0; i<NUM_READERS; i++) { 
          shared_news->read[i] = false;
	}
	sleep(rand() % 3);

        // signal the fact that new items may be consumed
        pthread_cond_broadcast(&shared_news->cond_readers);
        pthread_mutex_unlock(&shared_news->mutex);
    }

    // never reached
    return NULL;
}

// consume random numbers
void* consumer(void *arg) {
    thread_info *this_thread = (thread_info*)arg;
    news_t *shared_news = this_thread->shared_news;
    int thread_num = this_thread->thread_num;
    int i;
    bool allread = true;
    char news[MAX_NEWS_SIZE];

    printf("Consumer Thread Started.\n");
    while(1) {
        pthread_mutex_lock(&shared_news->mutex);

        if(shared_news->read[thread_num] == true) { // empty
            // wait for new items to be appended to the shared_news
            pthread_cond_wait(&shared_news->cond_readers, &shared_news->mutex);
        }

	strcpy(news, shared_news->news_buf);
        shared_news->read[thread_num] = true;
        printf("Thread: %d Consumed news - %s\n", thread_num, news);
	allread = true;
	for (i=0; i<NUM_READERS; i++) { 
          if (shared_news->read[i] == false) {
            allread = false;
            break;
	  }
        }
        if (allread == true) {
          memset(shared_news->news_buf, '\0', MAX_NEWS_SIZE);
          pthread_cond_signal(&shared_news->cond_portal);
        }

        pthread_mutex_unlock(&shared_news->mutex);
    }

    return NULL;
}

int main(int argc, char *argv[]) {
 
    int i;
    news_t shared_news =  {PTHREAD_MUTEX_INITIALIZER, PTHREAD_COND_INITIALIZER, PTHREAD_COND_INITIALIZER};
    thread_info reader_threads[NUM_READERS];
    pthread_t threads[NUM_READERS+1];

    for (i=0; i<NUM_READERS; i++) {
      shared_news.read[i] = true;
    }
    printf("About to create portal thread\n");	
    pthread_create(&threads[0], NULL, portal, (void*)&shared_news);
    printf("About to create reader threads\n");	
    for (i=0; i<NUM_READERS; i++) {
      reader_threads[i].thread_num = i;
      reader_threads[i].shared_news = &shared_news;
      pthread_create(&threads[i+1], NULL, consumer, (void*)&(reader_threads[i]));
    }

    for (i=0; i<=NUM_READERS; i++) {
      pthread_join(threads[i], NULL);
    }

    return 0;
}
