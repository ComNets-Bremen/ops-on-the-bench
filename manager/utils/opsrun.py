#!/usr/bin/env python3
#
# The code called by the worker.py to execute
# OPS simulations and collect results.
#
# Author: Asanga Udugama (adu@comnets.uni-bremen.de)
# Date: 03-April-2020
#
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['agg.path.chunksize'] = 100000
import matplotlib.pyplot as plt
import csv
import subprocess
import os
import glob
import time
import fpdf
try:
    import dropboxops
except ModuleNotFoundError:
    from . import dropboxops
import threading
import enum
import datetime

OUTPUT_FOLDER = '/opt/data'
STAT_LIST = '/opt/OPS/simulations/stat-list.txt'
NET_LIST = '/opt/OPS/simulations/net-list.txt'
ARCHIVE_FILE = 'results.zip'
ARCHIVE_LIST = ['INFO.txt', 'omnetpp.ini', 'graphs', 'csv', 'simrun']
STATUSVALS = enum.Enum('STATUSVALS', 'INITILIZING SIMULATING PARSING ARCHIVING UPLOADING TERMINATING COMPLETED CRASHED', start=1)
MONITOR_INTERVAL_SEC = 3.0
ARCHIVE_LIFETIME_DAYS = 365
ESTIMATED_TOTAL_RESULTS_SIZE_PERC = 20.0

# main entry point for performing a single job,
# i.e., running a single OPS simulation
def run_ops(job, arguments):

    # init common variables used by main thread and the monitor thread
    lock = threading.Lock()
    common = {'job': job,
              'status': STATUSVALS.INITILIZING,
              'start_time': time.time()
             }

    # start monitor thread 
    monitor_thread = threading.Thread(target=monitor, args=(common, lock))
    monitor_thread.start()
    
    try:

        # get the job idenifier (used to uniquely identify all 
        # output)
        with lock:
            job_id = str(common['job'].get_id())

        # make output folders
        root_folder, graphs_folder, csv_folder, simrun_folder, temp_folder = create_folders(job_id)

        # update root path
        with lock:
            common['root_folder'] = root_folder
            common['temp_folder'] = temp_folder

        # santize given omnetpp.ini
        sanitize_ini(root_folder, arguments['omnetpp.ini'])

        # set time after setup work and change status
        with lock:
            common['time_after_setup'] = time.time()
            common['status'] = STATUSVALS.SIMULATING

        # run simulations
        run_sim(root_folder, arguments['runconfig'], common, lock)
    
        # update final percentage, set time after simulation and status
        with lock:
            update_sim_progress(common)
            common['time_after_sim'] = time.time()
            common['status'] = STATUSVALS.PARSING

        # create graphs from vectors 
        create_graphs(root_folder, graphs_folder, temp_folder, common, lock)

        # set time after creating graphs
        with lock:
            common['time_after_graphs'] = time.time()

        # create scalar stats
        create_stats(root_folder, graphs_folder, csv_folder, temp_folder)

        # set time after creating scalar stats 
        with lock:
            common['time_after_scalar_stats'] = time.time()

        # create resolution changed CSV
        create_csv(root_folder, csv_folder, temp_folder, arguments['summarizing_precision'])

        # set time after creating summarized vector data
        with lock:
            common['time_after_summary_data'] = time.time()

        # create simulator performance stats
        create_sim_stats(root_folder, simrun_folder, common, lock)

        # update final percentage and set time after creating simulator performance stats
        with lock:
            update_results_progress(common)
            common['time_after_sim_stats'] = time.time()
    
        # create INFO file
        create_info_file(root_folder, arguments['summarizing_precision'], common, lock)

        # set status
        with lock:
            common['status'] = STATUSVALS.ARCHIVING

        # create an archive file of results to return
        archive_path = create_archive(root_folder, ARCHIVE_FILE, ARCHIVE_LIST)

        # set time after archive creation & status
        with lock:
            common['time_after_arch'] = time.time()
            common['status'] = STATUSVALS.UPLOADING

        # handle archive file as requested
        shared_link = upload_archive(archive_path, arguments['storage_backend_id'], arguments['storage_backend_token'], keep_days=ARCHIVE_LIFETIME_DAYS)

        # set time after arch file upload and status
        with lock:
            common['time_after_arch_upload'] = time.time()
            common['shared_link'] = shared_link
            common['status'] = STATUSVALS.TERMINATING

        # remove all folders and files created
        remove_files(root_folder)

        # set time after file removal and status
        with lock:
            common['time_after_file_removal'] = time.time()
            common['status'] = STATUSVALS.COMPLETED

        # update whatever final values before returning
        with lock:
            job.meta['shared_link'] = shared_link
            job.save_meta()

        # wait for monitor thread to finish
        monitor_thread.join()

        # return the created link's URL
        return shared_link

    except:

        # cleanup after a failure
        if 'root_folder' in common:
            cleanup_after_crash(common['root_folder'])

        # set time after file removal and status
        with lock:
            common['time_after_file_removal'] = time.time()
            job.save_meta()

        # wait for monitor thread to finish
        monitor_thread.join()
        
        raise


# make output folders
def create_folders(job_id):

    print('creating folders ...')

    # create the root output folder
    root_folder = os.path.join(OUTPUT_FOLDER, job_id)
    os.mkdir(root_folder)

    # make graphs folder
    graphs_folder = os.path.join(root_folder, 'graphs')
    os.mkdir(graphs_folder)

    # make CSV folder
    csv_folder = os.path.join(root_folder, 'csv')
    os.mkdir(csv_folder)

    # make simulation run details folder
    simrun_folder = os.path.join(root_folder, 'simrun')
    os.mkdir(simrun_folder)
    
    # make CSV folder
    temp_folder = os.path.join(root_folder, 'temp')
    os.mkdir(temp_folder)

    return root_folder, graphs_folder, csv_folder, simrun_folder, temp_folder


# santize given omnetpp.ini
def sanitize_ini(root_folder, omnetppini):

    # create the original ini file
    originipath = os.path.join(root_folder, 'orig-omnetpp.ini')
    with open(originipath, 'w') as ofp:
         ofp.write(omnetppini)

    # place the omnetpp.ini in simulations folder
    inipath = './omnetpp.ini'
    inifp = open(inipath, 'w')
    
    # place a copy of the omnetpp.ini in the job folder
    inicopypath = os.path.join(root_folder, 'omnetpp.ini')
    inicfp = open(inicopypath, 'w')

    # read original ini and create a santized versions
    with open(originipath, 'r') as ofp:
        for line in ofp:
            row = line.split('=')
            if 'result-dir' in row[0].strip() \
                 or 'output-vector-file' in row[0].strip() \
                 or 'output-scalar-file' in row[0].strip():
                inifp.write('# --- sanitizer commented out --- -' + line)
                inicfp.write('# --- sanitizer commented out --- -' + line)
            else:
                inifp.write(line)
                inicfp.write(line)


# run simulations
def run_sim(root_folder, runconfig, common, lock):

    print('starting simulation ...')

    # path of the sanitized .ini file
    inipath = './omnetpp.ini'

    # create the simulation activity log
    logpath = os.path.join(root_folder, 'ops.log')
    logfp = open(logpath, 'w')
 
    # create results location option
    results_dir = '--result-dir=' + root_folder
 
    # run simulation
    proc = subprocess.Popen(['ops-simu', '-r', '0', '-m', '-u', 'Cmdenv', 
                    '-n', '.:../src:../modules/inet/src:../modules/KeetchiLib/src',
                    '--image-path=../modules/inet/images',
                    results_dir,
                    '-l', 'INET', '-l', 'keetchi', 
                    inipath], 
                    stdout=logfp, stderr=subprocess.STDOUT)

    # update info for simulation monitoring
    with lock:
        common['sim_proc_id'] = proc.pid
        common['sim_log_file'] = logpath        
    
    # wait for simulation to end
    proc.wait()

    # finish
    logfp.close()


# create stat graphs
def create_graphs(root_folder, graphs_folder, temp_folder, common, lock):

    print('creating graphs ...')

    with open(STAT_LIST,'r') as listfp:
        lines = csv.reader(listfp, delimiter=',')
        for row in lines:
            if row[0].strip().startswith('#'):
                continue

            # get parameters
            stat_name = row[0].strip()
            stat_layer = row[1].strip()
            stat_unit = row[2].strip()
            stat_dtype = row[3].strip()
            stat_acctype = row[4].strip()
            stat_scastat = row[5].strip()
            stat_var = row[6].strip()

            # create stat search filter
            net_str = ''
            with open(NET_LIST,'r') as netfp:
                netlines = csv.reader(netfp, delimiter=',')
                for netrow in netlines:
                    if netrow[0].strip().startswith('#'):
                        continue
                    net_str += ('module(' + netrow[0].strip() + ') OR ')
                net_str += ('module(ABCD)')
            filter_str = '\"attr:configname(General) AND attr:runnumber(0) AND (' + net_str + ') AND name(' + stat_var + ':vector)\"'

            # build path of temporary CSV file
            temp_csv = os.path.join(temp_folder, (stat_var + '.csv'))
            if os.path.exists(temp_csv):
                os.remove(temp_csv)

            # build search path for .vec file (created by simulation)
            search_path = ''
            wildcard = glob.glob(root_folder + '/*.vec')
            for vecfile in wildcard:
                search_path = vecfile
                break

            # create the activity log
            logpath = os.path.join(graphs_folder, 'stat-creation.log')
            logfp = open(logpath, 'a')

            # run scave tool extract vector data
            proc = subprocess.Popen(['scavetool', 'export', '-v', '-f', filter_str,
                                 '-o', temp_csv, '-F', 'CSV-S', search_path],
                                 stdout=logfp, stderr=subprocess.STDOUT)

            # update info for results creation process monitoring
            with lock:
                common['results_proc_id'] = proc.pid

            # wait for process to end
            proc.wait()

            # close log file
            logfp.close()
            
            # create x, y arrays to plot from the created CSV
            x = []
            y = []
            with open(temp_csv,'r') as csvfp:
                dlines = csv.reader(csvfp, delimiter=',')
                for i, drow in enumerate(dlines):
                    if i == 0:
                        continue
                    x.append(float(drow[0].strip()))
                    if stat_dtype == 'int':
                        if 'Inf' in drow[1].strip():
                            y.append(0)
                        else:
                            y.append(int(drow[1].strip()))
                    else:
                        if 'Inf' in drow[1].strip():
                            y.append(0.0)
                        else:
                            y.append(float(drow[1].strip()))

            # build graph path
            graph_path = os.path.join(graphs_folder, (stat_var + '.pdf'))

            # plot graph
            if x != [] and y != []:
                plt.figure(figsize=(12, 4))
                plt.grid(True)
                plt.plot(x, y, '-', rasterized=True)
                plt.xlabel('Simulation Time (seconds)')
                plt.ylabel(stat_name + '\n(' + stat_unit + ')')
                plt.title(stat_name)
                plt.tight_layout()
                plt.savefig(graph_path)
                plt.close()


def create_stats(root_folder, graphs_folder, csv_folder, temp_folder):

    print('creating scalar stats ...')

    # setup .pdf writer to write results
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 10, 'Scalar Results', 0, 1)

    # build path and open scalar stat CSV file
    scalar_csv = os.path.join(csv_folder, 'scalar-stats.csv')
    ocsvfp = open(scalar_csv,'w')
            
    # write heading lines
    ocsvfp.write('# stat, type, value\n')

    # get the results
    with open(STAT_LIST,'r') as listfp:
        lines = csv.reader(listfp, delimiter=',')
        for row in lines:
            if row[0].strip().startswith('#'):
                continue

            # get parameters
            stat_name = row[0].strip()
            stat_layer = row[1].strip()
            stat_unit = row[2].strip()
            stat_dtype = row[3].strip()
            stat_acctype = row[4].strip()
            stat_scastat = row[5].strip()
            stat_var = row[6].strip()

            # create stat search filter
            net_str = ''
            with open(NET_LIST,'r') as netfp:
                netlines = csv.reader(netfp, delimiter=',')
                for netrow in netlines:
                    if netrow[0].strip().startswith('#'):
                        continue
                    net_str += ('module(' + netrow[0].strip() + ') OR ')
                net_str += ('module(ABCD)')
            filter_str = '\"attr:configname(General) AND attr:runnumber(0) AND (' + net_str + ') AND name(' + stat_var + ':' + stat_scastat + ')\"'

            # build path of temporary CSV file
            temp_csv = os.path.join(temp_folder, (stat_var + '-sca.csv'))

            # build search path for .vec file (created by simulation)
            search_path = ''
            wildcard = glob.glob(root_folder + '/*.sca')
            for scafile in wildcard:
                search_path = scafile
                break

            # create the activity log
            logpath = os.path.join(graphs_folder, 'stat-creation.log')
            logfp = open(logpath, 'a')

            # run scave tool extract vector data
            subprocess.call(['scavetool', 'export', '-v', '-f', filter_str,
                                 '-o', temp_csv, '-F', 'CSV-S', search_path],
                                 stdout=logfp, stderr=subprocess.STDOUT)

            # close log file
            logfp.close()

            # get and write the output created by the scavetool
            with open(temp_csv,'r') as csvfp:
                dlines = csv.reader(csvfp, delimiter=',')
                for i, drow in enumerate(dlines):
                    if i == 0:
                        continue
                    if stat_dtype == 'int':
                        val = 0 if 'Inf' in drow[4].strip() or 'NaN' in drow[4].strip() else int(drow[4].strip())
                        wline = '%s, %s - %s %s' % (stat_layer, stat_name, '{:,d}'.format(val), stat_unit)
                        cline = '%s, %s, %d\n' % (stat_var, stat_scastat, val)
                    else:
                        val = 0.0 if 'Inf' in drow[4].strip() or 'NaN' in drow[4].strip() else float(drow[4].strip())
                        wline = '%s, %s - %s %s' % (stat_layer, stat_name, '{:,.2f}'.format(val), stat_unit)
                        cline = '%s, %s, %f\n' % (stat_var, stat_scastat, val)

                    # write .pdf file
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(40, 10, wline, 0, 1)

                    # write .csv file
                    ocsvfp.write(cline)

                    break


    # create the .pdf file
    results_path = os.path.join(graphs_folder, 'scalar-stats.pdf')
    pdf.output(results_path, 'F')

    # close scalar stat .csv
    ocsvfp.close()


# create resolution changed CSV
def create_csv(root_folder, csv_folder, temp_folder, summarizing_precision):
    
    print('creating CSV files ...')

    with open(STAT_LIST,'r') as listfp:
        lines = csv.reader(listfp, delimiter=',')
        for row in lines:
            if row[0].strip().startswith('#'):
                continue

            # get parameters
            stat_name = row[0].strip()
            stat_layer = row[1].strip()
            stat_unit = row[2].strip()
            stat_dtype = row[3].strip()
            stat_acctype = row[4].strip()
            stat_scastat = row[5].strip()
            stat_var = row[6].strip()

            # build path of original CSV file
            orig_csv = os.path.join(temp_folder, (stat_var + '.csv'))

            # build path and open summarized CSV file
            new_csv = os.path.join(csv_folder, (stat_var + '.csv'))
            ocsvfp = open(new_csv,'w')
            
            # write heading lines
            wline = '# ' + stat_name + '\n# simtime, ' + stat_var + '\n'
            ocsvfp.write(wline)

            # write data based on type of data
            if stat_dtype == 'int' and stat_acctype == 'same':
                with open(orig_csv,'r') as icsvfp:
                    dlines = csv.reader(icsvfp, delimiter=',')
                    val = 0
                    nexttime = summarizing_precision
                    for i, drow in enumerate(dlines):
                        if i == 0:
                            continue
                        while nexttime < float(drow[0].strip()):
                            wline = '%f, %d\n' % (nexttime, val)
                            ocsvfp.write(wline)
                            nexttime = nexttime + summarizing_precision
                        val = val if 'Inf' in drow[1].strip() else int(drow[1].strip())
                    wline = '%f, %d\n' % (nexttime, val)
                    ocsvfp.write(wline)

            elif stat_dtype == 'float' and stat_acctype == 'same':
                with open(orig_csv,'r') as icsvfp:
                    dlines = csv.reader(icsvfp, delimiter=',')
                    val = 0.0
                    nexttime = summarizing_precision
                    for i, drow in enumerate(dlines):
                        if i == 0:
                            continue
                        while nexttime < float(drow[0].strip()):
                            wline = '%f, %f\n' % (nexttime, val)
                            ocsvfp.write(wline)
                            nexttime = nexttime + summarizing_precision
                        val = val if 'Inf' in drow[1].strip() else float(drow[1].strip())
                    wline = '%f, %f\n' % (nexttime, val)
                    ocsvfp.write(wline)

            else:
                pass
            
            ocsvfp.close()


# create simulator related stats
def create_sim_stats(root_folder, simrun_folder, common, lock):

    # setup .pdf writer to write results
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 10, 'Simulation Run Statistics', 0, 1)

    # build path and open scalar stat CSV file
    scalar_csv = os.path.join(simrun_folder, 'simrun-stats.csv')
    ocsvfp = open(scalar_csv,'w')
            
    # write heading lines
    ocsvfp.write('# stat, value, description\n')
    
    # get details of simulation (events, duration, etc.)
    sim_time_sec = 0.0
    clock_time_sec = 0.0
    ev_per_sec = 0.0
    simsec_per_sec = 0.0
    ev_per_simsec = 0.0
    total_events = 0
    msgs_created = 0
    results_proc_time = 0.0

    # get details from the simulation log
    ops_log = os.path.join(root_folder, 'ops.log')
    with open(ops_log,'r') as ilogfp:
        required_pos = False
        for line in ilogfp:
            if 'Elapsed:' in line and '100% completed' in line:
                required_pos = True
                total_events = int(line.partition('Event #')[2].strip().split(' ')[0])
                clock_time_sec = float(line.partition('Elapsed:')[2].strip().split(' ')[0].replace('s', ''))
                sim_time_sec = float(line.partition('t=')[2].strip().split(' ')[0])

            elif required_pos and 'Speed:' in line:
                ev_per_sec = float(line.partition('ev/sec=')[2].strip().split(' ')[0])
                simsec_per_sec = float(line.partition('simsec/sec=')[2].strip().split(' ')[0])
                ev_per_simsec = float(line.partition('ev/simsec=')[2].strip().split(' ')[0])

            elif required_pos and 'Messages:' in line:
                msgs_created = int(line.partition('created:')[2].strip().split(' ')[0])

    # get time of results processing and peak disk usage
    with lock:
        results_proc_time = common['time_after_summary_data'] - common['time_after_sim']
        peak_disk = common['peak_disk_usage'] if 'peak_disk_usage' in common else 0
        peak_sim_ram_usage = common['peak_sim_ram_usage'] if 'peak_sim_ram_usage' in common else 0
        peak_results_ram_usage = common['peak_results_ram_usage'] if 'peak_results_ram_usage' in common else 0
        start_time = common['start_time']

    # write .pdf with sim details
    pdf.set_font('Arial', '', 9)
    pdf.cell(40, 10, ('Start Wall Clock Time - ' + time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_time))), 0, 1)
    pdf.cell(40, 10, ('Simulation Run Wall Clock Time - {:,} seconds'.format(clock_time_sec)), 0, 1)
    pdf.cell(40, 10, ('Simulated Time - {:,} seconds'.format(sim_time_sec)), 0, 1)
    pdf.cell(40, 10, ('Total Events - {:,} events'.format(total_events)), 0, 1)
    pdf.cell(40, 10, ('Events per Wall Clock Second - {:,} events'.format(ev_per_sec)), 0, 1)
    pdf.cell(40, 10, ('Simulation Seconds per Wall Clock Second - {:,} seconds'.format(simsec_per_sec)), 0, 1)
    pdf.cell(40, 10, ('Events per Simulation Second - {:,} events'.format(ev_per_simsec)), 0, 1)
    pdf.cell(40, 10, ('Total Messages Created -  {:,} messages'.format(msgs_created)), 0, 1)
    pdf.cell(40, 10, ('Results Parsing Wall Clock Time - {:,} seconds'.format(results_proc_time)), 0, 1)
    pdf.cell(40, 10, ('Total Wall Clock Time - {:,} seconds'.format(clock_time_sec + results_proc_time)), 0, 1)
    pdf.cell(40, 10, ('Peak Disk Space Used - {:,} bytes'.format(peak_disk)), 0, 1)
    pdf.cell(40, 10, ('Peak RAM Used (Simulation) - {:,} bytes'.format(peak_sim_ram_usage)), 0, 1)
    pdf.cell(40, 10, ('Peak RAM Used (Results Parsing) - {:,} bytes'.format(peak_results_ram_usage)), 0, 1)

    # write .csv file
    ocsvfp.write(('startclocktimeepochsec, %f, Start Wall Clock Time in Epoch seconds\n' % (start_time)))
    ocsvfp.write(('simrunclocktimesec, %f, Simulation Run Wall Clock Time in seconds\n' % (clock_time_sec)))
    ocsvfp.write(('simtimesec, %f, Simulated Time in seconds\n' % (sim_time_sec)))
    ocsvfp.write(('totevents, %d, Total Events\n' % (total_events)))
    ocsvfp.write(('evperclocktime, %f, Events per Wall Clock Second\n' % (ev_per_sec)))
    ocsvfp.write(('simsecperclocktime, %f, Simulation Seconds per Wall Clock Second\n' % (simsec_per_sec)))
    ocsvfp.write(('evpersimtime, %f, Events per Simulation Second\n' % (ev_per_simsec)))
    ocsvfp.write(('totmsgs, %d, Total Messages Created\n' % (msgs_created)))
    ocsvfp.write(('resultsparsingclocktimesec, %f, Results Parsing Wall Clock Time in seconds\n' % (results_proc_time)))
    ocsvfp.write(('totaljobclocktimesec, %f, Total Wall Clock Time in seconds\n' % (clock_time_sec + results_proc_time)))
    ocsvfp.write(('peakdiskspaceusedbytes, %d, Peak Disk Space Used in bytes\n' % (peak_disk)))
    ocsvfp.write(('peakramusedsimbytes, %d, Peak RAM Used (Simulation) in bytes\n' % (peak_sim_ram_usage)))
    ocsvfp.write(('peakramusedresultsbytes, %d, Peak RAM Used (Results Parsing) in bytes\n' % (peak_results_ram_usage)))

    # create the .pdf file
    results_path = os.path.join(simrun_folder, 'simrun-stats.pdf')
    pdf.output(results_path, 'F')

    # close scalar stat .csv
    ocsvfp.close()


# create INFO file
def create_info_file(root_folder, summarizing_precision, common, lock):

    # get things to show in info file
    with lock:
        start_time = common['start_time']

    # build path and open info file
    info_file = os.path.join(root_folder, 'INFO.txt')
    oinfofp = open(info_file,'w')
            
    # write info
    oinfofp.write('This zip archive contains the following files and folders of the simulation run on ' \
                    + time.strftime('%d %B %Y at %H:%M:%S.\n\n', time.gmtime(start_time)))
    oinfofp.write('* omnetpp.ini - The configuration file used by the simulation.\n')
    oinfofp.write('* pdf         - The folder containing all the scalar and vector results as graphs.\n')
    oinfofp.write('* csv         - The folder containing scalar and vector results summarized in ' \
                                + ('%s second intervals.\n' % ('{:,.2f}'.format(summarizing_precision))))
    oinfofp.write('* simrun      - The folder containing information about the simulation run (e.g., events generated).\n')
    oinfofp.write('* INFO.txt    - This file.\n\n')

    # close info file
    oinfofp.close()


# create an archive file of results to return
def create_archive(root_folder, archive_file, archive_list):

    # build path of archive file
    archive_path = os.path.join(root_folder, archive_file)

    # save current path and change to root folder
    cwd = os.getcwd()
    os.chdir(root_folder)

    # build the zip command array
    cmd = ['zip', '-r', archive_path]
    for entry in archive_list:
        cmd.append(entry)

    # run command
    subprocess.call(cmd)

    # set to original path
    os.chdir(cwd)

    return archive_path


# handle (e.g., upload) archive file
def upload_archive(archive_path, storage_id, token, keep_days=7):

    shared_link = ''
    if 'dropbox' in storage_id:
        # use DropBox with given token
        shared_link = dropboxops.upload_file(archive_path, token, livetime=datetime.timedelta(days=keep_days))
    else:
        # move to some place in local storage (not implemented)
        pass

    return shared_link


# remove all created files and folders
def remove_files(root_folder):

    # build command
    cmd = ['rm', '-rf', root_folder]

    # run command
    subprocess.call(cmd)


# cleanup after crash
def cleanup_after_crash(root_folder):

    # do clean up activities
    
    # if job folder exists, remove
    if not os.path.isdir(root_folder):
        return
        
    # build command
    cmd = ['rm', '-rf', root_folder]

    # run command
    subprocess.call(cmd)


# thread that monitors all activities and reports regularly
def monitor(common, lock):

    print('starting monitor thread ...')
    
    while True:
        
        # wait for some time
        time.sleep(MONITOR_INTERVAL_SEC)

        # check what state the simulation job is in 
        # and collect progress information
        with lock:
            
            # check current status and call the computation functions
            if common['status'] == STATUSVALS.INITILIZING:
                pass

            elif common['status'] == STATUSVALS.SIMULATING:
                update_peak_disk_usage(common)
                update_peak_ram(common, 'sim')
                update_sim_progress(common)

            elif common['status'] == STATUSVALS.PARSING:
                update_peak_disk_usage(common)
                update_peak_ram(common, 'results')
                update_results_progress(common)

            elif common['status'] == STATUSVALS.ARCHIVING:
                update_peak_disk_usage(common)

            # adjusting the results parsing progress in case the estimation
            # went wrong
            if common['status'].value > STATUSVALS.PARSING.value:
                common['results_completed_perc'] = 100

            # update job with status data
            job = common['job']
            job.meta['start_time_str'] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(common['start_time']))
            job.meta['peak_disk_usage'] = common['peak_disk_usage'] if 'peak_disk_usage' in common else 0
            job.meta['peak_sim_ram_usage'] = common['peak_sim_ram_usage'] if 'peak_sim_ram_usage' in common else 0
            job.meta['peak_results_ram_usage'] = common['peak_results_ram_usage'] if 'peak_results_ram_usage' in common else 0
            job.meta['sim_completed_perc'] = common['sim_completed_perc'] if 'sim_completed_perc' in common else 0
            job.meta['results_completed_perc'] = common['results_completed_perc'] if 'results_completed_perc' in common else 0
            job.meta['current_state'] = common['status'].name
            job.save_meta()

            # if completed or crashed, then stop thread
            if common['status'].value >= STATUSVALS.COMPLETED.value:
                break

            # # dump all dict values
            # dump_dict(job.meta, common)


    print('finishing monitor thread ...')

# # dump dictionary values to a file
# def dump_dict(meta, common):
#     debugfile = os.path.join(common['root_folder'], 'debug.txt')
#     with open(debugfile, 'a') as dfp:
#         print('===', datetime.date.today(), '===\n', file=dfp)
#         print('===== meta =====\n', file=dfp)
#         for key in meta:
#             print(key, ':', meta[key], '\n', file=dfp)
#         print('===== common =====\n', file=dfp)
#         for key in common:
#             print(key, ':', common[key], '\n', file=dfp)


# find peak disk usage
def update_peak_disk_usage(common):

    # get root folder
    root_folder = common['root_folder'] if 'root_folder' in common else None
    if not root_folder:
        return

    # get disk space used
    current_use = 0
    for folder_path, folder_names, file_names in os.walk(root_folder):
        for f in file_names:
            fp = os.path.join(folder_path, f)
            if not os.path.islink(fp):
                current_use += os.path.getsize(fp)

    # update peak disk usage
    peak_disk_usage = common['peak_disk_usage'] if 'peak_disk_usage' in common else 0
    common['peak_disk_usage'] = current_use if peak_disk_usage < current_use else peak_disk_usage


# find peak RAM use for given process
def update_peak_ram(common, proc_type):
    
    # get peak RAM for the simulation process
    if 'sim' in proc_type and 'sim_proc_id' in common:
        pid_path = '/proc/' + str(common['sim_proc_id']) + '/status'
        try:
            result = subprocess.check_output(['grep', 'VmPeak', pid_path], stderr=subprocess.STDOUT)
        except:
            peak_sim_ram_usage = common['peak_sim_ram_usage'] if 'peak_sim_ram_usage' in common else 0
            common['peak_sim_ram_usage'] = peak_sim_ram_usage      
            return

        vals = result.split()
        if len(vals) < 3 or not vals[1].isdigit():
            return

        peak_sim_ram_usage = common['peak_sim_ram_usage'] if 'peak_sim_ram_usage' in common else 0
        current_ram_peak = int(vals[1]) * 1024
        common['peak_sim_ram_usage'] = current_ram_peak if peak_sim_ram_usage < current_ram_peak else peak_sim_ram_usage        

    # get peak RAM for the results parsing process
    elif 'results' in proc_type and 'results_proc_id' in common:
        pid_path = '/proc/' + str(common['results_proc_id']) + '/status'
        try:
            result = subprocess.check_output(['grep', 'VmPeak', pid_path], stderr=subprocess.STDOUT)
        except:
            peak_results_ram_usage = common['peak_results_ram_usage'] if 'peak_results_ram_usage' in common else 0
            common['peak_results_ram_usage'] = peak_results_ram_usage
            return

        vals = result.split()
        if len(vals) < 3 or not vals[1].isdigit():
            return

        peak_results_ram_usage = common['peak_results_ram_usage'] if 'peak_results_ram_usage' in common else 0
        current_ram_peak = int(vals[1]) * 1024
        common['peak_results_ram_usage'] = current_ram_peak if peak_results_ram_usage < current_ram_peak else peak_results_ram_usage


# get sim completed percentage percentage
def update_sim_progress(common):

    # get temp folder
    temp_folder = common['temp_folder'] if 'temp_folder' in common else None
    if not temp_folder:
        return

    # get ops.log file path
    logpath = common['sim_log_file'] if 'sim_log_file' in common else None
    if not logpath or not os.path.exists(logpath):
        return

    # create the log extract file
    temppath = os.path.join(temp_folder, 'temp.log')

    # extract the lower part of log
    subprocess.call(['cp', logpath, temppath])

    # get last line with the completed percentage
    lastline = None
    with open(temppath, 'r') as tempfp:
        for line in tempfp:
            if 'Elapsed:' in line and 'total' in line:
                lastline = line

    # check if line there
    if not lastline:
        return

    # parse line to get percentage
    lastperc = lastline.partition('completed  (')[2].split('%')[0]
    if not lastperc.isdigit():
        return
    common['sim_completed_perc'] = round(float(lastperc))


# estimate results processing completed percentage
def update_results_progress(common):

    # get root folder
    root_folder = common['root_folder'] if 'root_folder' in common else None
    if not root_folder:
        return

    # get disk space used (in the process get also the .vec file)
    total_size = 0
    vec_file = None
    for folder_path, folder_names, file_names in os.walk(root_folder):
        for f in file_names:
            fp = os.path.join(folder_path, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
                if 'vec' in os.path.splitext(fp)[1]:
                    vec_file = fp

    # vec file not there?
    if not vec_file:
        return

    # compute results percentage completed
    # computation: assume the results files sizes will add up to a percetage
    #              (ESTIMATED_TOTAL_RESULTS_SIZE_PERC) of .vec file size
    vec_size = os.path.getsize(vec_file)
    estimated_total_results_size = vec_size * ESTIMATED_TOTAL_RESULTS_SIZE_PERC / 100.0
    current_results_size = total_size - vec_size
    results_completed_perc = round(current_results_size / estimated_total_results_size * 100.0)
    common['results_completed_perc'] = results_completed_perc if results_completed_perc <= 100 else 100
