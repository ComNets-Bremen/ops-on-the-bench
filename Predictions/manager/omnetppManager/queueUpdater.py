import redis
from rq import Queue
import pickle
import json
import requests

if __name__ == '__main__':
    
    r = redis.Redis(host='192.168.142.128', port=6379, password='d9f9ef5f2fef8da852b43c58c7f1c6c1')
    #r = redis.Redis(host='127.0.0.1', port=6379, password='d9f9ef5f2fef8da852b43c58c7f1c6c1')
    
    url = "http://192.168.142.128:8000/omnetppManager/get-simulation-details/"
    response = requests.get(url)
    
    if response.status_code == 200:
        simdata = response.json()
        #print(simdata)
    else:
        print("No Simulation Content was read")
        
        
    url2 = "http://192.168.142.128:8000/omnetppManager/get-server-resources/"
    response2 = requests.get(url2)
    
    if response2.status_code == 200:
        servdata = response2.json()
        print(type(servdata))
    else:
        print("No Server Content was read")
        
    
    dicts = {}
    for key,value in servdata.items():
        #print(key)
        disk = {}
        max_ram = 0
        max_disk = 0
        for k,v in value.items():
            if k=="max_ram":
                max_ram = v
            elif k=="max_disk_space":
                max_disk = v
            disk['max_ram'] = max_ram
            disk['max_disk_space'] = max_disk
            
            dicts[key] = disk
        
    print("FINAL DICTIONARY : ",dicts)
    
    Tm = 0
    Tds = 0
    #TAKING SERVER 1 INFORMATION ONLY
    for key,value in dicts.items():
        server = key
        Tm = int(value['max_ram'])
        Tds = int(value['max_disk_space'])
        break
    
    print("Totals : ",Tm,Tds)
    q = Queue(connection=r)
    jobs_ids = q.job_ids
    print("Jobs Currently On The Queue: ", jobs_ids)
    
    Disk_InUse = 0
    RAM_InUse = 0
    
    running_jobs = q.jobs
    running_jobs = [job for job in running_jobs if job.get_status()=='started']
    
    for job in running_jobs:
    
        for key,value in simdata.items():
        
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
                ru = max(peak_simram,peak_resram)
                Disk_InUse = Disk_InUse + du
                RAM_InUse = RAM_InUse + ru
    
    #print("Disk In Use: ", Disk_InUse)
    #print("RAM IN USE : ", RAM_InUse)         
    
    Disk_Avail = round(max(0,Tds-Disk_InUse)*1e-9,2)
    #Disk_Avail = 10
    RAM_Avail = round(max(0,Tm-RAM_InUse)*1e-9,2)
    #RAM_Avail = 3.8
    
    print("Availabile Resources on the Server: ","Disk : "+str(Disk_Avail)+" GB","RAM : "+str(RAM_Avail)+" GB")
    
    queued_jobs = q.jobs
    queued_jobs = [job for job in queued_jobs if job.get_status()=='queued']
    
    
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
                
                    if len(queued_jobs)>1 and q.get_job_position(job)!=0 and queued_jobs[0]!=job:
                        #job.cancel()
                        job.delete()
                        print("Job Deleted")
                        q.enqueue_job(job,at_front=True)
                        print("Q's order Changed")
                        flag = True
                        break
                    else:
                        flag = True
                        break
                else:
                    print("Q's order Unchanged")
        if flag:
            #print("Q's Changed or first job is ok")
            break
    
    
    queued_jobs_status = [job.id for job in queued_jobs if job.get_status()=='queued']
    
    print("Updated Jobs Order On The Queue : ", queued_jobs_status)
    r.close()
                

