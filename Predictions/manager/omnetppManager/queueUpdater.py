import redis
from rq import Queue
import pickle
import json
import requests
from rq import Worker

if __name__ == '__main__':
    
    r = redis.Redis(host='192.168.142.128', port=6379, password='d9f9ef5f2fef8da852b43c58c7f1c6c1')
    #r = redis.Redis(host='127.0.0.1', port=6379, password='d9f9ef5f2fef8da852b43c58c7f1c6c1')
    
#--------------------------RETRIEVING WORKER INFORMATION---------------------------------------------------------    
    workers = Worker.all(connection=r)
    
    idles = 0
    for worker in workers:
        if worker.state=='idle':
            idles = idles+1
    print("No of idle workers : ",idles)
    
    if idles>0:
    
        JobsInProgress = []
        print("Connected workers:")
        for worker in workers:
            print("Worker",worker.name)
            current_job = worker.get_current_job()
            try:
                if current_job.is_started:
                    print("Job is in progress",current_job.id)
                    JobsInProgress.append(current_job)
                else:
                    print("No job is currently in progress")
            except:
                print("No Current Job")
        print("----------------------------------------------------------")
            
#----------------------------RETRIEVING STORED PREDICTION VALUES-----------------------------------------------            
    
        url = "http://192.168.142.128:8000/omnetppManager/get-simulation-details/"
        headers1 = {'HTTP-X-HEADER-ID':'123456789'}
        response = requests.get(url,headers=headers1)
    
        if response.status_code == 200:
            simdata = response.json()
            #print("simulation data", simdata)
        else:
            print("No Simulation Content was read")
        
#-----------------------------RETRIEVING SERVER CONFIGURATION----------------------------------------------------        
    #url2 = "http://192.168.142.128:8000/omnetppManager/get-server-resources/"
    
    
        url2 = "http://192.168.142.128:8000/omnetppManager/get-server-config/"
    
        headers = {'HTTP-X-HEADER-SERVER-ID':'uranus',
		    			'HTTP-X-HEADER-TOKEN':'8103487f-9eb4-49e8-918d-a3d31bad2020'}
					
        response2 = requests.get(url2,headers=headers)
    
        if response2.status_code == 200:
            servdata = response2.json()
            #print(type(servdata))
        else:
            print("No Server Content was read")
        
    
        dicts = {}
        for key,value in servdata.items():
            max_ram = 0
            max_disk = 0
            disk = {}
            li = []
        
            for dic in value:      
                for k,v in dic.items():
                    li.append(v)               
                          
            for i in range(len(li)):
                if li[i]=='max_ram':
                    max_ram = li[i+1]
                elif li[i]=='max_disk_space':
                    max_disk = li[i+1]
            
                disk['max_ram'] = max_ram
                disk['max_disk_space'] = max_disk
            
                dicts[key] = disk
        
        #print("FINAL DICTIONARY : ",dicts)
        
#--------------------------------------FINDING MAXIMUM RESOURCES----------------------------------------------------
    
        Tm = 0
        Tds = 0
        #TAKING SERVER 1 INFORMATION ONLY
        for key,value in dicts.items():
            server = key
            Tm = round(int(value['max_ram'])*1e-9,2)
            Tds = round(int(value['max_disk_space'])*1e-9,2)
            break
    
        print("Totals : ",Tm,Tds)
    
#-------------------------------------FINDING AVAILABLE RESOURCES----------------------------------------------------
    
        dq = Queue(connection=r)    
        q = Queue('secondary', connection=r)
    
        jobs_ids = q.job_ids
        #print("Jobs Currently On The Queue: ", jobs_ids)
    
        Disk_InUse = 0
        RAM_InUse = 0
    
        #running_jobs = dq.jobs
        #running_jobs = [job for job in running_jobs if job.get_status()=='started']
    
        print("Total Jobs in Progress ",JobsInProgress)
    
        for job in JobsInProgress:
    
            for key,value in simdata.items():
                #print(key)
        
                if key == str(job.id):
                    du = 0
                    peak_simram = 0
                    peak_resram = 0
                
                    for k in value.keys():
                        if k == "predicted_peak_disk":
                            du = value[k]
                        elif k == "predicted_peak_RAM_Sim":
                            peak_simram = value[k]
                        elif k == "predicted_peak_RAM_Res":
                            peak_resram = value[k]
                
                    print("Resources Used by ", key, du, peak_simram, peak_resram)        
                    ru = max(peak_simram,peak_resram)
                    Disk_InUse = Disk_InUse + du
                    RAM_InUse = RAM_InUse + ru
    
        print("Disk In Use: ", Disk_InUse)
        print("RAM IN USE : ", RAM_InUse)         
    
        Disk_Avail = max(0,Tds-Disk_InUse)
        #Disk_Avail = 40
        RAM_Avail = max(0,Tm-RAM_InUse)
        #RAM_Avail = 8
        print("Availabile Resources on the Server: ","Disk : "+str(Disk_Avail)+" GB","RAM : "+str(RAM_Avail)+" GB")
        print("----------------------------------------------------------")
  
#-------------------------------------UPDATING DEFAULT QUEUE------------------------------------------------------------

    
        queued_jobs = q.jobs
        queued_jobs = [job for job in queued_jobs if job.get_status()=='queued']
    
        #print("Jobs on the Secondary Queue : ", queued_jobs)
    
        flag = False
    
        for job in queued_jobs:
    
            for key,value in simdata.items():
        
                if key == str(job.id):
            
                    qdu = 0
                    qpeak_simram = 0
                    qpeak_resram = 0
                
                    for k in value.keys():
                        if k == "predicted_peak_disk":
                            qdu = value[k]
                        elif k == "predicted_peak_RAM_Sim":
                            qpeak_simram = value[k]
                        elif k == "predicted_peak_RAM_Res":
                            qpeak_resram = value[k]
                    qru = max(qpeak_simram,qpeak_resram)
                
                    #print("Resources Required by Simulation", key, str(qdu)+" GB", str(qpeak_simram)+" GB", str(qpeak_resram)+" GB") 
                
                    print("Resources Required by Simulation", key, 
                    "Disk :"+ str(qdu)+" GB", "RAM : "+ str(qru) +" GB") 
                    if qdu<=Disk_Avail and qru<=RAM_Avail:
                
                        #if len(queued_jobs)>1 and q.get_job_position(job)!=0 and queued_jobs[0]!=job:
                        #job.cancel()
                        job.delete()
                        print("Job Deleted")
                        dq.enqueue_job(job,at_front=True)
                        #print("Q's order Changed")
                        print("Job Moved to  Default Queue")
                        flag = True
                        break
                        #else:
                            #flag = True
                            #break
                    else:
                        print("Q's order Unchanged")
            if flag:
                #print("Q's Changed or first job is ok")
                break
    
#-------------------------PRINTING AVAILABLE JOBS IN DEFAULT/SECONDARY QUEUES-----------------------

        dq1 = Queue(connection=r)    
        q1 = Queue('secondary', connection=r)
    
        queued_jobs_status = [job.id for job in q1.jobs if job.get_status()=='queued']
    
        #print("Jobs Order On The SECONDARY Queue : ", queued_jobs_status)
    
        now_running_jobs = dq1.jobs
    
        default_jobs_status = [job.id for job in now_running_jobs if job.get_status()=='queued']
    
        #print("Queued Jobs On The DEFAULT Queue : ", now_running_jobs)
        r.close()
        
    else:
        print("No Worker is IDLE")
                

