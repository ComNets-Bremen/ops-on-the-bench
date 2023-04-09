import numpy as np
import pandas as pd
import re
import glob

# Function that takes in the JSON File and return a list of tuples where each tuple is (Run_Config, Omnetpp.ini, TargetsDictionary)
def JSONExtractor(JSON):
    runINI = []
    delINI = []
    ignore = []
    disk = "'peakdiskspaceusedbytes'"
    simRAM = "'peakramusedsimbytes'"
    resRAM = "'peakramusedresultsbytes'"
    time = "'totaljobclocktimesec'"

    for i in range(len(JSON)):

        # Checking if the Simulation_Completion and Results_Parsing_Completion are 100% and current state = 'COMPLETED'
        if ((JSON.simulations[i]['meta']['sim_completed_perc'] == 100) and (
                JSON.simulations[i]['meta']['results_completed_perc'] == 100) and (
                JSON.simulations[i]['meta']['current_state'] == 'COMPLETED')):

            # Checking if simulation contains meta data with 'sim_runtime_stats' as key (if not present 'totaljobclocktimesec' param can't be found, so discarding them)
            if 'sim_runtime_stats' in JSON.simulations[i]['meta']:

                # Fetching the all 4 targets variables from meta data of the simulation
                dicts = {'peakdiskspaceusedbytes': re.compile(disk + r'\,\s([0-9\.]+)').findall(
                    str(JSON.simulations[i]['meta']['sim_runtime_stats'])),
                         'peakramusedsimbytes': re.compile(simRAM + r'\,\s([0-9\.]+)').findall(
                             str(JSON.simulations[i]['meta']['sim_runtime_stats'])),
                         'peakramusedresultsbytes': re.compile(resRAM + r'\,\s([0-9\.]+)').findall(
                             str(JSON.simulations[i]['meta']['sim_runtime_stats'])),
                         'totaljobclocktimesec': re.compile(time + r'\,\s([0-9\.]+)').findall(
                             str(JSON.simulations[i]['meta']['sim_runtime_stats']))}

                # Appending Run_Config, Omnetpp.ini and Targets dictionary as a tuple in runINI list
                runINI.append((JSON.simulations[i]['runconfig'], JSON.simulations[i]['omnetppini'], dicts))
            else:
                ignore.append((JSON.simulations[i]['runconfig'], JSON.simulations[i]['omnetppini']))
        else:
            # print(i)
            # Appending info about incomplete simulations
            delINI.append((JSON.simulations[i]['runconfig'], JSON.simulations[i]['omnetppini'], dicts))

    return runINI

# Function that takes in Run_Config, .ini, TargetsDictionary and returns a dictionary of all .ini parameters
# of a simulation along with their corresponding targets
def FeatureExtractor(runconfig,omnetppini,targets):
  if not runconfig == 'General':
    # print(runconfig)
    # replacing multiple \r and \n with null and \n resp. and splitting on \n basis
    splitINI = re.sub(r'[\n]+','\n ',re.sub(r'[\r]+','',omnetppini)).strip().split('\n')

    # INI filtering (removes any redundant commands/comments starting with '#' in the ini)
    refreshINI = ''.join([line.strip() for line in splitINI if not line.strip().startswith('#')])

    # RunConfig Filtering (Filter INI for the specific RunConfig) --- case where mutiple Run_Configs
    # are present in same ini file
    configFiltered = re.compile(runconfig + r'[\'\]\n\#\s\w\*\.=\(\)\"\,\-\/\+]+').findall(refreshINI)

    # Extracting every ini param and converting to dict
    paramDict = dict(re.findall(r'\*\*\.([a-zA-Z\.]+) = ([A-Za-z0-9\"\.\/\-]+)',str(configFiltered)))
    if 'numNodes' not in paramDict.keys():
      x = re.findall(r'\*\*\.(numNodes) = ([0-9]+)',refreshINI)[0]
      paramDict[x[0]] = x[1]

    # Combining .ini parameters dictionary with TargetsDictionary
    paramDict.update(targets)

    return paramDict

# PATH to JSON data files directory
path = "./directory"

JSONDrives = glob.glob('path/*.json')
print(len(JSONDrives))
print(JSONDrives)

finalDic = []
inis = []
runconfig = []
for path in JSONDrives:
  try:
    json = pd.read_json(path)
    JsonFiltered = JSONExtractor(json)
    # print("Initial Length of JSON",len(json),"Final Length of Filtered JSON",len(JsonFiltered))
    # ParamsList = []
    for rc,ini,targets in JsonFiltered:
      # Feature Extractor function returns .ini params and targets as dictionary
      dic = FeatureExtractor(rc,ini,targets)
      if bool(dic):
        # ParamsList.append(dic)
        inis.append(ini)
        runconfig.append(rc)
        finalDic.append(dic)
  except:
    print("Path Error")

# Data Cleaning
# Different column categories
Numericals = ['app_dataGenerationInterval','constraintAreaMaxX','constraintAreaMaxY','mobility_noOfLocations','mobility_Hosts',
              'mobility_speed','numNodes','app_dataSizeInBytes','forwarding_maximumCacheSize','mobility_nodeId']
Categoricals = ['applicationLayer','forwardingLayer','linkLayer','mobilityType']
Targets = ['peakdiskspaceusedbytes','peakramusedsimbytes','peakramusedresultsbytes','totaljobclocktimesec']

first = pd.DataFrame(finalDic)

for_null = first[first['forwardingLayer'].isna()]
second = first[~first['forwardingLayer'].isna()]

second.columns = second.columns.str.replace('.','_',regex=False)

remove_cols = ['app_popularityAssignmentPercentage','app_usedRNG','forwarding_antiEntropyInterval','forwarding_maximumHopCount','forwarding_usedRNG','link_wirelessRange','link_neighbourScanInterval','link_bandwidthBitRate','link_wirelessHeaderSize','link_usedRNG','constraintAreaMinX','constraintAreaMinY','constraintAreaMinZ','constraintAreaMaxZ','updateInterval','mobility_initFromDisplayString','mobility_popularityDecisionThreshold','mobility_returnHomePercentage','mobility_neighbourLocationLimit','mobility_radius','mobility_alpha','mobility_waitTime','mobility_usedRNG','app_dataGenerationIntervalMode','app_trafficInfoPath','forwarding_spraywaitFlavour','forwarding_noDuplicate','mobility_traceFile','link_contactTracesPath','forwarding_broadcastRRS','forwarding_sendOnNeighReportingFrequency','forwarding_sendFrequencyWhenNotOnNeighFrequency','forwarding_pEncounterMax','forwarding_pEncounterFirst','forwarding_pFirstThreshold','forwarding_alpha','forwarding_beta','forwarding_gamma','forwarding_delta','forwarding_standardTimeInterval','forwarding_agingInterval','forwarding_neighbourhoodChangeSignificanceThreshold','forwarding_coolOffDuration','forwarding_learningConst','forwarding_backoffTimerIncrementFactor','app_specificDestination','app_specificDestinationNodeName','app_ttl','forwarding_useTTL']

leftover_cols = [col for col in second.columns if col not in remove_cols]

# Seprating dataframe with required columns
third = second[leftover_cols]

# Filling Missing Values and Replacing
third.mobilityType = third.mobilityType.fillna("ContactTraces")
third.mobility_nodeId = third.mobility_nodeId.fillna('0').str.replace('-1','1')
third.constraintAreaMaxX = third.constraintAreaMaxX.fillna('0')
third.constraintAreaMaxY = third.constraintAreaMaxY.fillna('0')
third.mobility_noOfLocations = third.mobility_noOfLocations.fillna('0')
third.mobility_Hosts = third.mobility_Hosts.fillna('0')
third.mobility_speed = third.mobility_speed.fillna('0')
third.forwarding_maximumCacheSize = third.forwarding_maximumCacheSize.fillna('0')

# Creating ONE-HOTS for categorical (object) columns
one_hots = pd.get_dummies(third[Categoricals],drop_first=True)
fourth = pd.concat([third,one_hots],axis=1)
fourth = fourth.drop(Categoricals,axis=1)

# Changing Numerical features from strings to integers
fourth['app_dataGenerationInterval'] =  fourth.app_dataGenerationInterval.apply(lambda x : x.replace('s','') if 's' in x else x)
fourth['constraintAreaMaxX'] =  fourth.constraintAreaMaxX.apply(lambda x : x.replace('m','') if 'm' in x else x)
fourth['constraintAreaMaxY'] =  fourth.constraintAreaMaxY.apply(lambda x : x.replace('m','') if 'm' in x else x)
fourth['mobility_speed'] =  fourth.mobility_speed.apply(lambda x : x.replace('mps','') if 'mps' in x else x)
def for_maxCache(cache):
  if 'bytes' in str(cache):
    return cache.replace('bytes','')
  elif 'byte' in str(cache):
    return cache.replace('byte','')
  else:
    return cache
fourth['forwarding_maximumCacheSize'] =  fourth.forwarding_maximumCacheSize.apply(lambda x : for_maxCache(x))

#Separating features from the dataset and changing their datatype
features = fourth.drop(Targets,axis=1)
fourth[features.columns] = features.apply(pd.to_numeric)

# Changing Target variables from string to integers
def target_list(target):
  if type(target) is list:
    return pd.to_numeric(target[0],errors='coerce')
for col in Targets:
  fourth[col] = fourth[col].apply(lambda x: target_list(x))

fourth.columns = fourth.columns.str.replace('"','')
fourth = fourth.reset_index(drop=True)
# print(fourth)

#Save the dataset
# fourth.to_csv('path.csv',index=False)