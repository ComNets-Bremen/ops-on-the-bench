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
import fpdf

OUTPUT_FOLDER = '/opt/data'
STAT_LIST = '/opt/OPS/simulations/stat-list.txt'
SUM_TIME_RES = 100.0

# main entry point for performing a single job,
# i.e., running a single OPS simulation
def run_ops(job_id, arguments):

    # make output folders
    root_folder, graphs_folder, csv_folder, temp_folder = create_folders(job_id)
    
    # run simulations
    run_sim(root_folder, arguments['omnetpp.ini'], arguments['runconfig'])
    
    # create graphs from vectors
    create_graphs(root_folder, graphs_folder, temp_folder)

    # create scalar stats
    create_stats(root_folder, graphs_folder, temp_folder)
    
    # create resolution changed CSV
    create_csv(root_folder, csv_folder, temp_folder)
    
    # # remove all temporary files
    # remove_temp(temp_folder)

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
    
    # make CSV folder
    temp_folder = os.path.join(root_folder, 'temp')
    os.mkdir(temp_folder)

    return root_folder, graphs_folder, csv_folder, temp_folder

# run simulations
def run_sim(root_folder, omnetppini, runconfig):

    print('starting simulation ...')

    # place the omnetpp.ini in simulations folder
    inipath = '/opt/OPS/simulations/omnetpp.ini'
    with open(inipath, 'w') as inifp:
         inifp.write(omnetppini)

    # place a copy of the omnetpp.ini in the job folder
    inicopypath = os.path.join(root_folder, 'omnetpp.ini')
    with open(inicopypath, 'w') as inicfp:
         inicfp.write(omnetppini)

    # create the simulation activity log
    logpath = os.path.join(root_folder, 'ops.log')
    logfp = open(logpath, 'w')
    
    # create results location option
    results_dir = '--result-dir=' + root_folder
    
    # run simulation
    subprocess.call(['/opt/OPS/ops-simu', '-r', '0', '-m', '-u', 'Cmdenv', 
                    '-n', '.:/opt/OPS/src:/opt/OPS//modules/inet/src:/opt/OPS/modules/KeetchiLib/src',
                    '--image-path=/opt/OPS/modules/inet/images',
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
            filter_str = '\"attr:configname(General) AND attr:runnumber(0) AND module(OPSHeraldNetwork) AND name(' + stat_var + ':vector)\"'

            # build path of temporary CSV file
            temp_csv = os.path.join(temp_folder, (stat_var + '.csv'))
            if os.path.exists(temp_csv):
                os.remove(temp_csv)

            # build search path for .vec file (created by simulation)
            search_path = os.path.join(root_folder, 'omnetpp.ini-General-0.vec')

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
            graph_file = stat_var + '.pdf'
            graph_path = os.path.join(graphs_folder, graph_file)

            # plot graph
            if x != [] and y != []:
                plt.figure(figsize=(12, 4))
                plt.grid(True)
                plt.plot(x, y, '-')
                plt.xlabel('Simulation Time (seconds)')
                plt.ylabel(stat_name + '\n(' + stat_unit + ')')
                plt.title(stat_name)
                plt.legend('')
                plt.tight_layout()
                plt.savefig(graph_path)
                plt.close()


def create_stats(root_folder, graphs_folder, temp_folder):

    print('creating stats ...')

    # setup .pdf writer to write results
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(40, 10, 'Simulation Scalar Results', 0, 1)

    # set positioning field
    
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
            filter_str = '\"attr:configname(General) AND attr:runnumber(0) AND module(OPSHeraldNetwork) AND name(' + stat_var + ':' + stat_scastat + ')\"'

            # build path of temporary CSV file
            temp_csv = os.path.join(temp_folder, (stat_var + '-sca.csv'))

            # build search path for .vec file (created by simulation)
            search_path = os.path.join(root_folder, 'omnetpp.ini-General-0.sca')

            # create the activity log
            logpath = os.path.join(graphs_folder, 'stat-creation.log')
            logfp = open(logpath, 'a')

            # run scave tool extract vector data
            subprocess.call(['scavetool', 'export', '-v', '-f', filter_str,
                                 '-o', temp_csv, '-F', 'CSV-S', search_path],
                                 stdout=logfp, stderr=subprocess.STDOUT)

            # close log file
            logfp.close()


            with open(temp_csv,'r') as csvfp:
                dlines = csv.reader(csvfp, delimiter=',')
                for i, drow in enumerate(dlines):
                    if i == 0:
                        continue
                    if stat_dtype == 'int':
                        val = 0 if 'Inf' in drow[4].strip() or 'NaN' in drow[4].strip() else int(drow[4].strip())
                        wline = '%s, %s - %s %s' % (stat_layer, stat_name, '{:,d}'.format(val), stat_unit)
                    else:
                        val = 0.0 if 'Inf' in drow[4].strip() or 'NaN' in drow[4].strip() else float(drow[4].strip())
                        wline = '%s, %s - %s %s' % (stat_layer, stat_name, '{:,.2f}'.format(val), stat_unit)
                    pdf.set_font('Arial', '', 9)
                    pdf.cell(40, 10, wline, 0, 1)
                    break

    # create the .pdf file
    results_path = os.path.join(graphs_folder, 'all-results.pdf')
    pdf.output(results_path, 'F')


# create resolution changed CSV
def create_csv(root_folder, csv_folder, temp_folder):
    
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
            wline = '# ' + stat_name + '\n# simtime, ' + stat_var
            ocsvfp.write(wline)

            # write data based on type of data
            if stat_dtype == 'int' and stat_acctype == 'same':
                with open(orig_csv,'r') as icsvfp:
                    dlines = csv.reader(icsvfp, delimiter=',')
                    val = 0
                    nexttime = SUM_TIME_RES
                    for i, drow in enumerate(dlines):
                        if i == 0:
                            continue
                        while nexttime < float(drow[0].strip()):
                            wline = '%f, %d\n' % (nexttime, val)
                            ocsvfp.write(wline)
                            nexttime = nexttime + SUM_TIME_RES
                        val = val if 'Inf' in drow[1].strip() else int(drow[1].strip())
                    wline = '%f, %d\n' % (nexttime, val)
                    ocsvfp.write(wline)

            elif stat_dtype == 'float' and stat_acctype == 'same':
                with open(orig_csv,'r') as icsvfp:
                    dlines = csv.reader(icsvfp, delimiter=',')
                    val = 0.0
                    nexttime = SUM_TIME_RES
                    for i, drow in enumerate(dlines):
                        if i == 0:
                            continue
                        while nexttime < float(drow[0].strip()):
                            wline = '%f, %f\n' % (nexttime, val)
                            ocsvfp.write(wline)
                            nexttime = nexttime + SUM_TIME_RES
                        val = val if 'Inf' in drow[1].strip() else float(drow[1].strip())
                    wline = '%f, %f\n' % (nexttime, val)
                    ocsvfp.write(wline)

            else:
                pass
            
            ocsvfp.close()


# remove all temporary files
def remove_temp(temp_folder):

    # remove all temp files
    wildcard = glob.glob(temp_folder + '/*.csv')
    for rmfile in wildcard:
        os.remove(rmfile)  

    # remove temp folder  
    os.rmdir(temp_folder)