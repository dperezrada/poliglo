# -*- coding: utf-8 -*-

from fabric.api import env, run
from fabric.colors import yellow
from fabric.context_managers import cd
from fabric.contrib.files import exists
from fabric.operations import put, sudo

from fab_utils import stage, upload_file, create_dir


# Add production user
def server_add_production_user(user):
    print yellow('\nAdding production user')
    sudo('adduser --disabled-password --gecos "" %s' % user)
    sudo('chown -R %s:%s /home/%s' % (user, user, user))


def install_redis():
    sudo("apt-get install -y redis-server")

# Install NodeJS
def server_install_node(user):
    sudo('wget -O - https://deb.nodesource.com/setup > /tmp/node_i')
    sudo('sudo bash /tmp/node_i > /dev/null')
    sudo('sudo apt-get install nodejs -y')
    sudo('sudo rm /tmp/node_i')
    create_dir('/home/%s/.npm' % user, user)

def server_install_dependencies():
    apt_packages = [
        "supervisor",
        "build-essential",
        "wget",
        "git",
        "nginx",
        "python-dev",
        "python-pip",
        "python-virtualenv",
        "python-lxml",
        "libxml2-dev",
        "libxslt1-dev",
        "zlib1g-dev"
    ]
    sudo('apt-get update')
    sudo('apt-get install -y %s' % ' '.join(apt_packages))

def ssh_config(user):
    if not exists('/home/%s/.ssh/authorized_keys' % user):
        sudo('mkdir -p /home/%s/.ssh' % user)
        sudo('cp /home/{ubuntu,%s}/.ssh/authorized_keys' % user)
        sudo('chown -R %s:%s /home/%s/.ssh' % (user, user, user))

def create_python_env(target_path, env_name, user):
    sudo('mkdir -p %s' % target_path, user=user)
    with cd(target_path):
        if not exists(env_name):
            sudo('virtualenv %s' % env_name, user=user)

def create_node_env(target_path, env_name, node_version, python_bin, user):
    if not exists('%s/%s' % (target_path, env_name)):
        sudo('%s/pip install nodeenv' % python_bin, user=user)
        sudo(
            '%s/nodeenv --node=%s --prebuilt %s/%s' % (
                python_bin, node_version, target_path, env_name
            ), user=user
        )

def install_enviroments():
    create_python_env(env.python_envs_path, env.python_env, env.deploy_user)
    create_node_env(env.node_envs_path, env.node_env, '0.12.2', env.python_bin, env.deploy_user)

def prepare_server():
    server_add_production_user(env.deploy_user)
    ssh_config(env.deploy_user)
    server_install_dependencies()
    install_redis()
    install_enviroments()
