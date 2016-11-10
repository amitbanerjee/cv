#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdbool.h>
#include<string.h>
#include<sys/socket.h>
#include<arpa/inet.h>

#define NUM_READERS 5             // Number of readers
#define MAX_NEWS_SIZE 1024        // Buffer size for news
#define PRODUCER_IP "127.0.0.1"   // News Producer's ip address
#define PORT 8080                 // port

typedef struct {
    pthread_mutex_t mutex; 	  // needed to add/remove data from the shared_news
    pthread_cond_t cond_portal;   // To notify Portal when all news are read
    pthread_cond_t cond_readers;  // To notify readers when new news arrives
    char news_buf[MAX_NEWS_SIZE]; // Place for readers to consume news
    bool read[NUM_READERS];       // Readers not yet read news
} news_t;

typedef struct {
    int       thread_num;         // Reader thread number
    news_t    *shared_news;       // Shared news between portal and readers
} thread_info;

// Portal thread
void* portal(void *arg) {

    news_t *shared_news = (news_t*)arg;
    int i, sock;
    bool allread;
    struct sockaddr_in server;
    char message[MAX_NEWS_SIZE] , server_reply[MAX_NEWS_SIZE];

    printf("Portal Thread Started.\n");
    
    //Create socket
    sock = socket(AF_INET , SOCK_STREAM , 0);
    if (sock == -1)
    {
        printf("Could not create socket");
        exit(1);
    }
    printf("Socket created\n");
     
    server.sin_addr.s_addr = inet_addr(PRODUCER_IP);
    server.sin_family = AF_INET;
    server.sin_port = htons( PORT );
 
    //Connect to remote server
    if (connect(sock , (struct sockaddr *)&server , sizeof(server)) < 0)
    {
        printf("connect failed. Error\n");
        exit(1);
    }
    printf("Connected to News Producer\n");

    while(1) {
        //Grab mutex lock
        pthread_mutex_lock(&shared_news->mutex);

        // Check id all readers read news
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
        if( recv(sock , server_reply , MAX_NEWS_SIZE , 0) <= 0)
        {
            printf("recv failed. Error.\n");
            exit(1);
        }
         
        printf("\nPortal received a new news - %s\n",server_reply);

	//Copy the news in the shared place
	strcpy(shared_news->news_buf, server_reply);
         
        //No readers yet read the news
	for (i=0; i<NUM_READERS; i++) { 
          shared_news->read[i] = false;
	}

        //Signal readers to consume the news
        pthread_cond_broadcast(&shared_news->cond_readers);
        pthread_mutex_unlock(&shared_news->mutex);
    }

    return NULL;
}

//Reader thread
void* reader(void *arg) {

    thread_info *this_thread = (thread_info*)arg;
    news_t *shared_news = this_thread->shared_news;
    int thread_num = this_thread->thread_num;
    int i;
    bool allread = true;
    char news[MAX_NEWS_SIZE];

    printf("Reader %d Thread Started.\n", thread_num);

    while(1) {
        //Grab the mutex lock first
        pthread_mutex_lock(&shared_news->mutex);

        //Check if the news is already read
        if(shared_news->read[thread_num] == true) {
            // wait for new news to be delivered
            pthread_cond_wait(&shared_news->cond_readers, &shared_news->mutex);
        }

	// New news is delivered, read it
	strcpy(news, shared_news->news_buf);
        shared_news->read[thread_num] = true;
        printf("Thread %d: Consumed news - %s\n", thread_num, news);

        // Now check if everybody else read the news
	allread = true;
	for (i=0; i<NUM_READERS; i++) { 
          if (shared_news->read[i] == false) {
            allread = false;
            break;
	  }
        }
        //Sleep some time to introduce randomness 
	sleep(((float)rand()/(float)(RAND_MAX)) * 2);
       
        //Everybody read it, now request for new news
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
      pthread_create(&threads[i+1], NULL, reader, (void*)&(reader_threads[i]));
    }

    for (i=0; i<=NUM_READERS; i++) {
      pthread_join(threads[i], NULL);
    }

    return 0;
}
