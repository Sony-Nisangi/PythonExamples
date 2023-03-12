import os
import shutil
from pathlib import Path
from filecmp import *
import filecmp

def isDirectoryEmpty(path):
    if os.path.exists(path) and not os.path.isfile(path):
        return not os.listdir(path)
    else:
        print("The path is either for a file or not valid")

def CreateDir(destDir):
    destdirPath = Path(destDir)
    if(not destdirPath.exists()):
        destdirPath.mkdir(parents=False,exist_ok=False)

def CopyDirectoryContents(source, replica):
    with os.scandir(source) as it:
            for entry in it:
                CopyItem(entry.path,replica)

def CopyItem(entry, replica):
    itemPath = Path(entry)
    if(itemPath.is_file()):
        msg = "file copied: "+ str(itemPath)
        print(msg)
        logging.info(msg)
        shutil.copy(itemPath, replica)
    elif(itemPath.is_dir()):
        destDir = Path(replica, itemPath.name)
        CreateDir(destDir)
        msg = "Copy directory [{}] contents".format(str(itemPath))
        print(msg)
        logging.info(msg)
        CopyDirectoryContents(itemPath, destDir)

def DeleteItem(entry):
    itemPath = Path(entry)
    if(itemPath.is_file()):
        msg = "file removed: "+ str(itemPath)
        print(msg)
        logging.info(msg)
        os.remove(itemPath)
    elif(itemPath.is_dir()):
        msg = "Remove directory [{}] and its contents".format(str(itemPath))
        print(msg)
        logging.info(msg)
        shutil.rmtree(itemPath, ignore_errors=True)

def CompareAndCopyDirs(sourceDirPath, replicaDirPath):
        compareResult = filecmp.dircmp(sourceDirPath, replicaDirPath)
        if(len(compareResult.left_only) > 0):
            # left only dirs - Just copy them (copy all folders & files inside in all levels)
            # left only files - just copy them
            for item in compareResult.left_only:
                 CopyItem(Path(sourceDirPath, item), replicaDirPath)
        if(len(compareResult.right_only) > 0):
            # right only dirs - Just delete them (delete all folders & files inside in all levels)
            # right only files - just delete them
            for item in compareResult.right_only:
                 DeleteItem(Path(replicaDirPath, item))
        # Same files - same (No need to copy)
        # diff files = Common files - same files ,  copy them to B
        if(len(compareResult.diff_files) > 0):
             for fileName in compareResult.diff_files:
                shutil.copy(Path(sourceDirPath, fileName),replicaDirPath)
        # Common dirs - use recursion to call above sequence
        if(len(compareResult.common_dirs) > 0):
             for dirName in compareResult.common_dirs:
                  CompareAndCopyDirs(Path(sourceDirPath, dirName), Path(replicaDirPath,dirName))

def SyncDirs(sourceDirPath: str, replicaDirPath: str):
    if(isDirectoryEmpty(sourceDirPath)):
        msg = "Source [{}] is empty! Enter a non-empty source directory!".format(sourceDirPath)
        print(msg)
        logging.info(msg)
    elif(not isDirectoryEmpty(replicaDirPath)):
        CompareAndCopyDirs(sourceDirPath, replicaDirPath)
    else:
        msg = ("Destination directory [{}] is empty, copying all the source contents!".format(replicaDirPath))
        print(msg)
        logging.info(msg)
        CopyDirectoryContents(sourceDirPath, replicaDirPath)

def StartSync(sc, timeInterval: int, source, replica): 
    print("Start sync...")
    logging.info("Start sync...")
    SyncDirs(source, replica)
    sc.enter(timeInterval, 1, StartSync, (sc,timeInterval, source, replica))


import sys
import sched, time, logging

if(len(sys.argv) < 5 and len(sys.argv)>5):
     print("Input arguments are not enough!, please specify source, target, time interval and log file path as inputs")
else:
    sourceDirPath = sys.argv[1]
    replicaDirPath = sys.argv[2]
    timeinterval = sys.argv[3]
    logFilePath = sys.argv[4]

    if(not os.path.exists(logFilePath)):
        os.makedirs(logFilePath)
    logFile = Path(logFilePath, "Sync.log")
    with open(logFile,'w') as f:
        logging.basicConfig(filename=logFile, filemode='w', level=logging.DEBUG)
        logging.info("Source path: {}".format(sourceDirPath))
        logging.info("Replica path: {}".format(replicaDirPath))
        logging.info("Sync time interval: {}".format(timeinterval))
        logging.info("Logfile path: {}".format(logFilePath))
        s = sched.scheduler(time.time, time.sleep)
        s.enter(0 , 1, StartSync, (s,int(timeinterval), sourceDirPath, replicaDirPath))
        s.run()