# -*- coding: utf-8 -*-
import os
import yaml
from collections import OrderedDict

from fabric.api import env, puts
from fabric.colors import yellow, cyan
from fabric.context_managers import cd
from fabric.contrib.files import exists
from fabric.operations import put, sudo

# START: from Stackoverflow http://stackoverflow.com/a/21912744/859731
def load_config_from_yaml(stream, loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(loader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)
# END

def stage(stage_name='staging'):
    # TODO: refactor this, read all variables
    puts("env.stage = %s" % stage_name, show_prefix=True)
    env.stage = stage_name
    env.current_local_dir = os.path.dirname(os.path.abspath(__file__))

    env.config_file = os.path.join(env.current_local_dir, "%s.yaml" % stage_name)
    env.config_data = load_config_from_yaml(open(env.config_file), yaml.SafeLoader)

    env.hosts = env.config_data['hosts']
    env.user = env.config_data['ssh_user']
    env.deploy_user = env.config_data['deploy_user']
    # quitar home
    env.deploy_path = env.config_data['deploy_path']
    env.monitor_local_path = env.config_data['monitor_local_path']
    env.poliglo_custom_path = env.config_data['poliglo_custom_path']
    env.envs_path = env.config_data['envs_path']
    env.local_tmp_path = env.config_data['local_tmp_path']
    env.poliglo_monitor_domain = env.config_data['poliglo_monitor_domain']
    env.poliglo_api_domain = env.config_data['poliglo_api_domain']
    env.poliglo_config_path = env.config_data['poliglo_config_path']
    env.poliglo_workflow_paths = env.config_data['poliglo_workflow_paths']
    env.supervisor_logs_path = env.config_data['supervisor_logs_path']
    env.poliglo_worker_paths = env.config_data['poliglo_worker_paths']

    general_config()


def general_config():
    env.use_ssh_config = True
    env.deploy_path = '/var/www'

    env.python_envs_path = '%s/python' % env.envs_path
    env.python_env = 'pydev'
    env.python_bin = '%s/%s/bin/' % (env.python_envs_path, env.python_env)
    env.python = '%s/%s/bin/python' % (env.python_envs_path, env.python_env)

    env.node_envs_path = '%s/node' % env.envs_path
    env.node_env = 'nodedev'
    env.node_bin = '%s/%s/bin' % (env.node_envs_path, env.node_env)
    env.node = '%s/%s/bin/node' % (env.node_envs_path, env.node_env)

def create_dir(path, user):
    sudo('mkdir -p %s' % path)
    sudo('chown %s:%s %s' % (user, user, path))

def upload_file(filename, target=None, user=None, tmp_path='/tmp'):
    if target is None:
        target = '%s/%s' % (tmp_path, filename)
    put(filename, target, use_sudo=True)
    if user:
        sudo('chown %s:%s %s' % (user, user, target))
    return target

def upload_text_to_file(text, target=None, user=None, local_tmp_path='/tmp'):
    from random import randint
    random_filepath = '%s/rand_file_%s' % (local_tmp_path, randint(0, 10000))
    with open(random_filepath, 'w') as rand_file:
        rand_file.write(text)
    upload_file(random_filepath, target, user=user)

def up_repos(target_path, repositories, user):
    print yellow('Downloading repositories')
    if not exists(target_path):
        create_dir(target_path, user)
    for repo in repositories:
        print cyan(repo['name'])
        update_repo(repo, target_path, user)

def update_repo(repo, parent_path, user):
    with cd(parent_path):
        if not exists(repo['short_name']):
            sudo('git clone %s' % repo['url'], user=user)
        else:
            with cd(repo['short_name']):
                sudo('git fetch --tags', user=user)
        with cd(repo['short_name']):
            sudo('git pull origin master', user=user)

def install_python_dep(parent_folder, folder_name, user, python_bin_path):
    with cd(parent_folder):
        with cd(folder_name):
            print yellow("Trying to install python deps to: %s" % folder_name)
            if exists('setup.py'):
                print cyan('Installing %s required python packages' % folder_name)
                sudo('%s/python setup.py develop' % python_bin_path, user=user)
            if exists('requirements.txt'):
                print cyan('Installing %s requirements python packages' % folder_name)
                sudo('%s/pip install -r requirements.txt' % python_bin_path, user=user)

def install_node_dep(parent_folder, folder_name, user, node_bin_path):
    with cd(parent_folder):
        with cd(folder_name):
            if exists('package.json'):
                print cyan('Installing %s required node packages' % folder_name)
                sudo('%s/npm install -d' % node_bin_path, user=user)
                sudo('%s/npm link' % node_bin_path, user=user)
