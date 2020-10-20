import sys
import time
import traceback
import subprocess


pods = [{
    "name": pod,
    "num_errors": 0,
    "last_tmp_tar_size": 0,
    "last_.redirector-data_tar_size": 0
} for pod in sys.argv[1:]]
while True:
    time.sleep(10)
    for pod in pods:
        if pod["num_errors"] >= 20:
            continue
        for dirname in ['.redirector-data', '/tmp']:
            if dirname == '/tmp':
                filename = 'tmp'
            else:
                filename = dirname
            kwargs = {"pod_name": pod["name"], "filename": filename, "dirname": dirname}
            returncode, output = subprocess.getstatusoutput("kubectl exec {pod_name} -- tar cvf {filename}.tar {dirname}".format(**kwargs))
            if returncode != 0:
                print(output)
                print('{pod_name} failed to tar {dirname}'.format(**kwargs))
                pod["num_errors"] += 1
                continue
            returncode, tarsize = subprocess.getstatusoutput("kubectl exec {pod_name} -- stat --format=%s {filename}.tar".format(**kwargs))
            if returncode != 0:
                print('{pod_name}: failed to get {filename}.tar size'.format(**kwargs))
                pod["num_errors"] += 1
                continue
            try:
                tarsize = int(tarsize)
            except Exception as e:
                traceback.print_exc()
                pod["num_errors"] += 1
                continue
            if tarsize > pod["last_{filename}_tar_size".format(**kwargs)]:
                print("Copying new tar for pod {pod_name} {filename} ({tarsize} bytes)".format(tarsize=tarsize, **kwargs))
                returncode, output = subprocess.getstatusoutput("kubectl cp {pod_name}:{filename}.tar redirector-data-{pod_name}-{filename}.tar".format(**kwargs))
                pod["last_{filename}_tar_size".format(**kwargs)] = tarsize

