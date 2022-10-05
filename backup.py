from datetime import datetime
import docker
import subprocess
import os
import boto3



##################
#    Config
##################

from config import *

##################
#   Functions
##################

def uploadBackupFile(file):
    relativePath = file[(len(backupDir)) + 1:]
    print("backup # upload file \"%s\" to s3://%s/%s/%s" % (file,awsS3_bucket,awsS3_path,relativePath))
    with open("%s" % file, "rb") as f:
        s3.upload_fileobj(f, awsS3_bucket, "%s/%s" %(awsS3_path, relativePath) )

def getVolumes(containerID):
    volumeOutput=subprocess.check_output([ '%s/helpers/inspect.sh' % ScriptRootDIR,containerID ]).decode('utf-8')
    volumes=[]
    for line in volumeOutput.split('\n'):
        if(len(line.strip()) > 0):
            parts = line.split()
            if(len(parts) > 4):
                if(parts[0] == "volume"):
                    volumeName = parts[1]
                    source = parts[2]
                    mount = parts[3]
                    volumes.append( [volumeName,source,mount] )
    return volumes

def backupContainer(containerID):
    print("========================")

    container = client.containers.get(containerID)

    # Get Attributes
    containerName = container.name
    containerImage = "unknown"
    if (len(container.image.tags) > 0 ):
        containerImage = container.image.tags[0]
    containerVolumes = getVolumes(container.id)

    # Starting
    print("backup # starting container backup \"%s\"" % containerName)
    print("backup # image is \"%s\"" % containerImage)

    if "mariadb:" in containerImage:
        print("mariadb # starting mariadb dump to \"var/lib/mysql/dump.sql\"")
        output = subprocess.check_output([ '%s/helpers/mariadb_prestep.sh' % ScriptRootDIR,containerID ]).decode('utf-8')
        
    if "postgres:" in containerImage:
        print("postgres # starting postgres dump to \"$PGDATA/dump.sql\"")
        output = subprocess.check_output([ '%s/helpers/postgres_prestep.sh' % ScriptRootDIR,containerID ]).decode('utf-8')



    for vol in containerVolumes:
        print("volumes # starting volume backup \"%s\"" % vol[0])
     
        currentDay = datetime.now().strftime("%d")
        destFolder = "%s/%s" % (backupDir, vol[0])
        destPath = "%s/daily_%s.tar" % (destFolder, currentDay)

        print("volumes # cleaning up old backups")
        subprocess.run(['rm','-rf',destFolder])
        subprocess.run(['mkdir','-p',destFolder])

        print("volumes # getting data from \"%s\" saving to \"%s\"" % (vol[2], destPath))

        f = open(destPath, 'wb')
        bits, stat = container.get_archive(vol[2])
        for chunk in bits:
            f.write(chunk)
        f.close()
        print("volumes # compressing \"%s\"" % (destPath))
        subprocess.run(['gzip','-f',destPath])
        uploadBackupFile("%s.gz" % destPath)


    print("backup # cleanup")
    if "mariadb:" in containerImage:
        print("mariadb # starting mariadb cleanup")
        output = subprocess.check_output([ '%s/helpers/mariadb_poststep.sh' % ScriptRootDIR,containerID ]).decode('utf-8')
        
    if "postgres:" in containerImage:
        print("postgres # starting postgres cleanup")
        output = subprocess.check_output([ '%s/helpers/postgres_poststep.sh' % ScriptRootDIR,containerID ]).decode('utf-8')


##################
#    Script
##################

ScriptRootDIR=os.path.dirname(os.path.realpath(__file__))

client = docker.from_env()

s3 = boto3.client('s3', 
    aws_access_key_id=awsS3_key_id, 
    aws_secret_access_key=awsS3_secret_key, 
    region_name="eu-west-1"
)


print("docker # export txt outputs")
output = subprocess.check_output([ '%s/helpers/docker_output.sh' % ScriptRootDIR, backupDir ]).decode('utf-8')
print("docker # upload txt outputs")
currentDay = datetime.now().strftime("%d")
uploadBackupFile("%s/docker_out/daily_%s_volumes.txt" % (backupDir, currentDay))
uploadBackupFile("%s/docker_out/daily_%s_ps.txt" % (backupDir, currentDay))


for container in client.containers.list():
    backupContainer(container.id)
