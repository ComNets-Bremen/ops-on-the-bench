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
matplotlib.rcParams['agg.path.chunksize'] = 10000
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

OUTPUT_FOLDER = '/opt/data'
STAT_LIST = '/opt/OPS/simulations/stat-list.txt'
NET_LIST = '/opt/OPS/simulations/net-list.txt'
ARCHIVE_FILE = 'results.zip'
ARCHIVE_LIST = ['INFO.txt', 'omnetpp.ini', 'graphs', 'csv', 'simrun']

# main entry point for performing a single job,
# i.e., running a single OPS simulation
def run_ops(job_id, arguments):

    # dictionary to store operation times
    op_times = {}
    
    # get start time of job
    op_times["start_time"] = time.time()

    # make output folders
    root_folder, graphs_folder, csv_folder, simrun_folder, temp_folder = create_folders(job_id)

    # santize given omnetpp.ini
    sanitize_ini(root_folder, arguments['omnetpp.ini'])

    # time after setup work
    op_times["time_after_setup"] = time.time()

    # run simulations
    run_sim(root_folder, arguments['runconfig'])
    
    # time after simulation
    op_times["time_after_sim"] = time.time()

    # create graphs from vectors
    create_graphs(root_folder, graphs_folder, temp_folder)

    # time after creating graphs
    op_times["time_after_graphs"] = time.time()

    # create scalar stats
    create_stats(root_folder, graphs_folder, csv_folder, temp_folder)

    # time after creating scalar stats
    op_times["time_after_scalar_stats"] = time.time()

    # create resolution changed CSV
    create_csv(root_folder, csv_folder, temp_folder, arguments['summarizing_precision'])

    # time after creating summarized vector data
    op_times["time_after_vec_data"] = time.time()

    # create simulator performance stats
    create_sim_stats(root_folder, simrun_folder, op_times)

    # time after creating simulator performance stats
    op_times["time_after_sim_stats"] = time.time()
    
    # create INFO file
    create_info_file(root_folder, arguments['summarizing_precision'])

    # create an archive file of results to return
    archive_path = create_archive(root_folder, ARCHIVE_FILE, ARCHIVE_LIST)

    # time after archive creation
    op_times["time_after_arch"] = time.time()

    # handle archive file as requested
    shared_link = ''
    if 'dropbox' in arguments['storage_backend_id']:
        # use DropBox with given token
        shared_link = dropboxops.upload_file(archive_path, arguments['storage_backend_token'])
    else:
        # move to some place in local storage
        pass

    # time after arch file upload
    op_times["time_after_arch_upload"] = time.time()

    # remove all folders and files created
    remove_files(root_folder)

    # time after file removal
    op_times["time_after_file_removal"] = time.time()

    # return the created link's URL
    return shared_link


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
def run_sim(root_folder, runconfig):

    print('starting simulation ...')

    # path of the sanitized .ini file
    inipath = './omnetpp.ini'

    # create the simulation activity log
    logpath = os.path.join(root_folder, 'ops.log')
    logfp = open(logpath, 'w')
 
    # create results location option
    results_dir = '--result-dir=' + root_folder
 
    # run simulation
    subprocess.call(['ops-simu', '-r', '0', '-m', '-u', 'Cmdenv', 
                    '-n', '.:../src:../modules/inet/src:../modules/KeetchiLib/src',
                    '--image-path=../modules/inet/images',
                    results_dir,
                    '-l', 'INET', '-l', 'keetchi', 
                    inipath], 
                    stdout=logfp, stderr=subprocess.STDOUT)

    logfp.close()


# create stat graphs
def create_graphs(root_folder, graphs_folder, temp_folder):

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
            subprocess.call(['scavetool', 'export', '-v', '-f', filter_str,
                                 '-o', temp_csv, '-F', 'CSV-S', search_path],
                                 stdout=logfp, stderr=subprocess.STDOUT)

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
def create_sim_stats(root_folder, simrun_folder, op_times):

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

    # get time of results processing 
    results_proc_time = op_times["time_after_vec_data"] - op_times["time_after_sim"]

    # get storage use
    total_used = 0
    for folder_path, folder_names, file_names in os.walk(root_folder):
        for f in file_names:
            fp = os.path.join(folder_path, f)
            if not os.path.islink(fp):
                total_used += os.path.getsize(fp)

    # write .pdf with sim details
    pdf.set_font('Arial', '', 9)
    pdf.cell(40, 10, ('Simulation Run Clock Time - %f seconds' % (clock_time_sec)), 0, 1)
    pdf.cell(40, 10, ('Simulated Time - %f seconds' % (sim_time_sec)), 0, 1)
    pdf.cell(40, 10, ('Total Events - %d events' % (total_events)), 0, 1)
    pdf.cell(40, 10, ('Events per Clock Second - %f events' % (ev_per_sec)), 0, 1)
    pdf.cell(40, 10, ('Simulation Seconds per Clock Second - %f seconds' % (simsec_per_sec)), 0, 1)
    pdf.cell(40, 10, ('Events per Simulation Second - %f events' % (ev_per_simsec)), 0, 1)
    pdf.cell(40, 10, ('Total Messages Created - %d' % (msgs_created)), 0, 1)
    pdf.cell(40, 10, ('Results Processing Clock Time - %f seconds' % (results_proc_time)), 0, 1)
    pdf.cell(40, 10, ('Total Job Clock Time - %f seconds' % (clock_time_sec + results_proc_time)), 0, 1)
    pdf.cell(40, 10, ('Total Storage Used - %d bytes' % (total_used)), 0, 1)

    # write .csv file
    ocsvfp.write(('simrunclocktimesec, %f, Simulation Run Clock Time in seconds\n' % (clock_time_sec)))
    ocsvfp.write(('simtimesec, %f, Simulated Time in seconds\n' % (sim_time_sec)))
    ocsvfp.write(('totevents, %d, Total Events\n' % (total_events)))
    ocsvfp.write(('evperclocktime, %f, Events per Clock Second\n' % (ev_per_sec)))
    ocsvfp.write(('simsecperclocktime, %f, Simulation Seconds per Clock Second\n' % (simsec_per_sec)))
    ocsvfp.write(('evpersimtime, %f, Events per Simulation Second\n' % (ev_per_simsec)))
    ocsvfp.write(('totmsgs, %d, Total Messages Created\n' % (msgs_created)))
    ocsvfp.write(('resultsprocclocktimesec, %f, Results Processing Clock Time in seconds\n' % (results_proc_time)))
    ocsvfp.write(('totaljobclocktimesec, %f, Total Job Clock Time in seconds\n' % (clock_time_sec + results_proc_time)))
    ocsvfp.write(('totalstorageusedbytes, %d, Total Storage Used in bytes\n' % (total_used)))

    # create the .pdf file
    results_path = os.path.join(simrun_folder, 'simrun-stats.pdf')
    pdf.output(results_path, 'F')

    # close scalar stat .csv
    ocsvfp.close()


# create INFO file
def create_info_file(root_folder, summarizing_precision):

    # build path and open info file
    info_file = os.path.join(root_folder, 'INFO.txt')
    oinfofp = open(info_file,'w')
            
    # write info
    oinfofp.write('This zip archive contains the following files and folders.\n\n')
    oinfofp.write('* omnetpp.ini - The configuration file used by the simulation.\n')
    oinfofp.write('* pdf         - The folder containing all the scalar and vector results as graphs.\n')
    oinfofp.write('* csv         - The folder containing scalar and vector results summarized in ' \
                                + ('%s second intervals.\n' % ('{:,.2f}'.format(summarizing_precision))))
    oinfofp.write('* simrun      - The folder containing info about the simulation run.\n')
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


# remove all created files and folders
def remove_files(root_folder):

    # build command
    cmd = ['rm', '-rf', root_folder]

    # run command
    subprocess.call(cmd)

