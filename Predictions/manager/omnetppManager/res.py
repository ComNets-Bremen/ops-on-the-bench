import os
import redis
from rq import Worker, Queue, Connection,get_current_job


# Define the job function
def test_simulation():
    # do something
    print("Executing job function")
    print("Arguments")
    #print(arguments)
    return {"status":"PASSED"}

if __name__ == '__main__':

    r = redis.Redis(host='192.168.142.128', port=6379, password='d9f9ef5f2fef8da852b43c58c7f1c6c1')
    queues = [Queue('default', connection=r)]
    # Create an RQ worker and tell it to listen to the queues
    with Connection(r):
        worker = Worker(queues)
        worker.work()
        print("Worker started")
