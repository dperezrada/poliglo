# -*- coding: utf-8 -*-

from fabric.api import env, run
from fabric.colors import yellow
from fabric.context_managers import cd
from fabric.contrib.files import exists
from fabric.operations import put, sudo

from fab_utils import upload_file, create_dir

# Add production user
def server_add_production_user():
    print yellow('\nAdding production user')
    sudo('adduser --disabled-password --gecos "" deploy')
    sudo('chown -R deploy:deploy /home/deploy')
    server_add_ssh_keys('deploy')


def server_add_ssh_keys(user):
    # Install repositories keys
    sudo('mkdir -p /home/%s/.ssh' % user, user=user)
    put('fab_files/ssh_configs/*', '/home/%s/.ssh/' % user, use_sudo=True)
    sudo('chown -R %s:%s /home/%s/.ssh' % (user, user, user, ))
    sudo('chmod 600 /home/%s/.ssh/*' % user)


def set_beanstalkd_config():
    upload_file('fab_files/beanstalkd.conf', '/etc/default/beanstalkd')
    run("sudo service beanstalkd restart")


def install_redis():
    sudo("apt-get install -y redis-server")
    sudo("service redis-server start")

# Install NodeJS
def server_install_node():
    sudo('wget -O - https://deb.nodesource.com/setup > /tmp/node_i')
    sudo('sudo bash /tmp/node_i > /dev/null')
    sudo('sudo apt-get install nodejs -y')
    sudo('sudo rm /tmp/node_i')
    create_dir('/home/%s/.npm' % env.deploy_user, env.deploy_user)

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

def deploy_ssh_config():
    if not exists('/home/deploy/.ssh/authorized_keys'):
        sudo('mkdir -p /home/deploy/.ssh')
        sudo('cp /home/{ubuntu,deploy}/.ssh/authorized_keys')
        sudo('chown -R deploy:deploy /home/deploy/.ssh')

def create_python_env():
    sudo('mkdir -p %s' % env.python_envs_path, user=env.deploy_user)
    with cd(env.python_envs_path):
        if not exists(env.python_env):
            sudo('virtualenv %s' % env.python_env, user=env.deploy_user)

def create_node_env():
    if not exists('%s/%s' % (env.node_envs_path, env.node_env)):
        sudo('%s/pip install nodeenv' % env.python_bin, user=env.deploy_user)
        sudo(
            '%s/nodeenv --node=0.12.2 --prebuilt %s/%s' % (
                env.python_bin, env.node_envs_path, env.node_env
            ), user=env.deploy_user
        )

def install_enviroments():
    create_python_env()
    create_node_env()

def prepare_server():
    server_add_production_user()
    deploy_ssh_config()
    server_install_dependencies()
    server_install_node()
    install_redis()
