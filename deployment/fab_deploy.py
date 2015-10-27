# -*- coding: utf-8 -*-
import os
from time import sleep

from fabric.api import env, run
from fabric.colors import yellow, cyan
from fabric.context_managers import cd
from fabric.contrib.files import exists
from fabric.operations import put, sudo, local

from fab_utils import stage, create_dir, upload_text_to_file, upload_file, up_repos, \
    install_python_dep, install_node_dep

REPOSITORIES = [
    {
        'name': 'Poliglo',
        'url': 'https://github.com/dperezrada/poliglo.git',
        'short_name': 'poliglo',
        'sub_repos': ['backend']
    }
]

def install_packages():
    print yellow('\nInstalling required packages')
    for repo in REPOSITORIES:
        install_python_dep(env.deploy_path, repo['short_name'], env.deploy_user, env.python_bin)
        install_node_dep(env.deploy_path, repo['short_name'], env.deploy_user, env.node_bin)
        update_config(repo['short_name'])
        for sub_repo in repo.get('sub_repos', []):
            path_to_sub_repo = os.path.join(repo['short_name'], sub_repo)
            install_python_dep(env.deploy_path, path_to_sub_repo, env.deploy_user, env.python_bin)
            install_node_dep(env.deploy_path, path_to_sub_repo, env.deploy_user, env.node_bin)
            update_config(path_to_sub_repo)


def upgrade_poliglo_client():
    sudo('%s/pip install poliglo --upgrade' % env.python_bin, user=env.deploy_user)

def setup_supervisor_poliglo():
    target_dir = '%s/workflows' % env.poliglo_custom_path
    create_dir(target_dir, env.deploy_user)
    supervisor_text = """[program:poliglo_server]
command=%s/python %s/poliglo/backend/poliglo_server/__init__.py
environment=POLIGLO_SERVER_URL=http://127.0.0.1:9015,CONFIG_PATH=%s/config.conf,WORKFLOWS_PATH=%s
stdout_logfile = %s/poliglo_server.log
stderr_logfile = %s/poliglo_server.err
""" % (env.python_bin, env.deploy_path, env.poliglo_custom_path, target_dir, \
        env.supervisor_logs_path, env.supervisor_logs_path)
    upload_text_to_file(
        supervisor_text,
        '/etc/supervisor/conf.d/poliglo_server.conf',
        local_tmp_path=env.local_tmp_path
    )

def create_workers_dir():
    workers_target_dir = "%s/workers/" % env.poliglo_custom_path
    create_dir(workers_target_dir, env.deploy_user)
    return workers_target_dir

def upload_scripts():
    scripts_path = os.path.join(env.poliglo_custom_path, 'scripts')
    create_dir(scripts_path, env.deploy_user)
    upload_file(
        "%s/scripts/*" % env.current_local_dir,
        scripts_path,
        user=env.deploy_user
    )
    sudo('chmod a+x %s/*.sh' % scripts_path)

def setup_supervisor_workers():
    workers_directory = create_workers_dir()
    for worker_dir in env.poliglo_worker_paths:
        # TODO improve the copy of these files
        upload_file(
            worker_dir, workers_directory, user=env.deploy_user
        )
    poliglo_base_workers_path = os.path.join(env.deploy_path, 'poliglo/workers')
    start_workers_script_path = '%s/scripts/start_workers.sh' % env.poliglo_custom_path
    print "exec_paths_py=%s SUPERVISOR_LOG_PATH=/var/log/supervisor SUPERVISOR_FILE=/tmp/workers_file_tmp CREATE_SUPERVISOR=1 WORKERS_PATHS=%s POLIGLO_SERVER_URL=http://127.0.0.1:9015 %s" % (env.python, workers_directory, start_workers_script_path)
    sudo(
        "exec_paths_py=%s SUPERVISOR_LOG_PATH=/var/log/supervisor SUPERVISOR_FILE=/tmp/workers_file_tmp CREATE_SUPERVISOR=1 WORKERS_PATHS=%s:%s POLIGLO_SERVER_URL=http://127.0.0.1:9015 %s" % (env.python, workers_directory, poliglo_base_workers_path, start_workers_script_path), user=env.deploy_user
    )
    sudo('mv /tmp/workers_file_tmp /etc/supervisor/conf.d/poliglo_workers.conf')


def restart_supervisor():
    sudo("ps -ef | grep supervisord | grep -v grep|awk '{print \"kill -s SIGTERM \"$2}'|/bin/bash")
    sleep(3)
    if exists('/tmp/supervisor.sock'):
        sudo("unlink /tmp/supervisor.sock")
    sudo("service supervisor start")


def update_poliglo_config():
    create_dir(env.poliglo_custom_path, env.deploy_user)
    upload_file(
        env.poliglo_config_path,
        '%s/config.conf' % env.poliglo_custom_path,
        user=env.deploy_user
    )

def update_poliglo_workflows():
    target = '%s/workflows' % env.poliglo_custom_path
    create_dir(target, env.deploy_user)
    for workflow_path in env.poliglo_workflow_paths or []:
        upload_file("%s/*" % workflow_path, target, user=env.deploy_user)

def install_workers_dependencies():
    install_script_path = '%s/scripts/install_workers_dependencies.sh' \
        % env.poliglo_custom_path
    workers_directories = [create_workers_dir(), ]
    sudo("PY_BIN_PATH=%s WORKERS_PATHS=%s %s" % (
            env.python_bin, ":".join(workers_directories), install_script_path
        ), user=env.deploy_user
    )

def update_config(repo_name):
    pass

def rm_supervisor_config():
    sudo('rm -f /etc/supervisor/conf.d/poliglo_workers.conf')
    sudo('rm -f /etc/supervisor/conf.d/poliglo_server.conf')

# Upload monitor
def generate_monitor_dist():
    local(
        'cd %s && npm install -d' % (
            env.monitor_local_path
        )
    )
    local(
        'cd %s && bower install -d' % (
            env.monitor_local_path
        )
    )
    local(
        'cd %s && POLIGO_API_URL=http://%s grunt build' % (
            env.monitor_local_path, env.poliglo_api_domain
        )
    )
    upload_file('%s/dist/' % env.monitor_local_path, '%s/' % env.deploy_path, user=env.deploy_user)
    monitor_path = '%s/monitor' % env.deploy_path
    if exists(monitor_path):
        sudo(
            'mv %s/monitor %s/monitor.old' % (env.deploy_path, env.deploy_path),
            user=env.deploy_user
        )
    sudo('mv %s/dist %s/monitor' % (env.deploy_path, env.deploy_path), user=env.deploy_user)
    if exists(monitor_path+'.old'):
        sudo('rm -rf %s/monitor.old' % env.deploy_path)

def restart_nginx():
    sudo("service nginx restart")

def upload_nginx_config_file():
    upload_text_to_file(
        open(
            "%s/fab_files/nginx_available/poliglo.conf" % env.current_local_dir
        ).read() % (env.poliglo_monitor_domain, env.deploy_path, env.poliglo_api_domain),
        '/etc/nginx/sites-available/poliglo.conf'
    )
    if not exists('/etc/nginx/sites-enabled/poliglo.conf'):
        sudo('ln -s /etc/nginx/sites-available/poliglo.conf /etc/nginx/sites-enabled/poliglo.conf')
    put('%s/fab_files/nginx.conf' % env.current_local_dir, '/etc/nginx/nginx.conf', use_sudo=True)

# TODO: Add this somewhere
# npm install -g handlebars

def update_repos_and_install():
    up_repos(env.deploy_path, REPOSITORIES, env.deploy_user)
    install_packages()
    upgrade_poliglo_client()

def update_workers():
    update_poliglo_config()
    update_poliglo_workflows()
    rm_supervisor_config()
    setup_supervisor_poliglo()
    restart_supervisor()
    sleep(10)
    upload_scripts()
    setup_supervisor_workers()
    install_workers_dependencies()
    restart_supervisor()

def update_monitor():
    generate_monitor_dist()

def update_nginx():
    upload_nginx_config_file()
    restart_nginx()

def deploy():
    update_repos_and_install()
    update_workers()
    update_monitor()
