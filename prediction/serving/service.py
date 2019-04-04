import time
import subprocess
from flask import Flask
from flask import request
import yaml
import json

app = Flask(__name__)
MODEL_DIR = 'gs://project-earth-kubeflow-model/landcover/4/metagraph'
JOB_NAMES = []


def make_job(name, in_file, output_file, yaml_file):
    global MODEL_DIR
    job = {'apiVersion': 'batch/v1',
           'kind': 'Job',
           'metadata': {'name': name},
           'spec': {'backoffLimit': 1,
                    'template': {'spec': {'containers': [
                        {'env': [{'name': 'GOOGLE_APPLICATION_CREDENTIALS',
                                  'value': '/opt/project-earth-2018-sa.json'},
                                 {'name': 'MODELDIR',
                                  'value': MODEL_DIR},
                                 {'name': 'INPUT',
                                  'value': in_file},
                                 {'name': 'OUTPUT',
                                  'value': output_file}],
                         'image': 'gcr.io/project-earth-2018/prediction',
                         'imagePullPolicy': 'Always',
                         'name': name,
                         'resources': {
                             'requests': {'memory': '4G', 'cpu': '2000m'}},
                         'volumeMounts': [
                             {'mountPath': '/secret/gcp-credentials',
                              'name': 'gcp-credentials',
                              'readOnly': True}]}],
                                          'restartPolicy': 'Never',
                                          'volumes': [
                                              {'name': 'gcp-credentials',
                                               'secret': {
                                                   'secretName': 'user-gcp-sa'}}]}}}}

    with open(yaml_file, 'w') as f:
        yaml.dump(job, f)


@app.route('/process', methods=['POST'])
def process_tfrecord():
    global JOB_NAMES
    data = request.get_json(silent=True)
    start_time = int(time.time() * 10)
    name = data.get('name', 'landcover-{}'.format(start_time))
    in_file = data['input']
    out_file = data['output']
    yaml_file = '/tmp/{}.yaml'.format(name)
    make_job(name, in_file, out_file, yaml_file)
    p = subprocess.Popen(
        ["kubectl", "-n", "kubeflow", "apply", "-f", yaml_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    output = p.communicate()
    JOB_NAMES.append(name)
    return json.dumps({'workload_name': name, 'output': str(output)})


@app.route('/delete', methods=['GET'])
def delete_jobs():
    global JOB_NAMES
    n = len(JOB_NAMES)
    for jn in JOB_NAMES:
        subprocess.call(["kubectl", "delete", "job", jn, "-n", "kubeflow"])
    JOB_NAMES.clear()
    return json.dumps({'deleted_jobs': n})


@app.route('/list', methods=['GET'])
def list_jobs():
    return json.dumps({'jobs': JOB_NAMES})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
