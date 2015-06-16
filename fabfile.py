import time

from fabric.api import *
from fabric.contrib.project import rsync_project

ACTIVATE = 'source {}/bin/activate'
UPDATE_REQS = '{} install -r {}requirements.txt'


@task
def dreamcatcher_cool():
    env.run = run
    env.cd = cd
    env.user = 'debian'
    env.name = 'dreamcatcher-cool'
    env.hosts = ['dreamcatcher-cool.local']
    env.path = '/srv/enso/'
    env.project = 'enso'
    env.virtualenv = 'virtualenv'
    env.environment = env.path + 'venv'
    env.warn_only = True
    env.python = 'source {0}venv/bin/activate && python'.format(env.path)
    env.pip = 'source {0}venv/bin/activate && pip'.format(env.path)
    env.restart = ('sudo /etc/init.d/enso stop', 'sudo /etc/init.d/enso start')


@task
def dreamcatcher_warm():
    env.run = run
    env.cd = cd
    env.user = 'debian'
    env.name = 'dreamcatcher-warm'
    env.hosts = ['dreamcatcher-warm.local']
    env.path = '/srv/enso/'
    env.project = 'enso'
    env.virtualenv = 'virtualenv'
    env.environment = env.path + 'venv'
    env.warn_only = True
    env.python = 'source {0}venv/bin/activate && python'.format(env.path)
    env.pip = 'source {0}venv/bin/activate && pip'.format(env.path)
    env.restart = ('sudo /etc/init.d/enso stop', 'sudo /etc/init.d/enso start')


@task
def lhc():
    env.run = run
    env.cd = cd
    env.user = 'pi'
    env.name = 'lhc'
    env.hosts = ['lhc.local']
    env.path = '/srv/enso/'
    env.project = 'enso'
    env.virtualenv = 'virtualenv'
    env.environment = env.path + 'venv'
    env.warn_only = True
    env.python = 'source {0}venv/bin/activate && python'.format(env.path)
    env.pip = 'source {0}venv/bin/activate && pip'.format(env.path)
    env.restart = ('sudo /etc/init.d/enso stop', 'sudo /etc/init.d/enso start')


@task
def bootstrap():
    upload()
    env.cd(env.path)
    env.run('rm -rf {0}'.format(env.environment))
    env.run('mkdir -p {0}'.format(env.environment))
    env.run('{0} {1}'.format(env.virtualenv, env.environment))
    update_requirements()


@task
def upload():
    extra_opts = '--omit-dir-times'
    put('requirements.txt', env.path)
    rsync_project(
        remote_dir=env.path,
        local_dir='.',
        delete=True,
        extra_opts=extra_opts,
        exclude=(
            '.git',
            'venv*/',
            '/venv2/'
            'fabfile.py',
            '*.pyc',
            '*.pyo'))


@task
def update_requirements():
    with prefix(ACTIVATE.format(env.environment)):
        env.run(UPDATE_REQS.format(env.pip, env.path))


@task
def restart():
    for command in env.restart:
        env.run(command)
        time.sleep(0.5)


@task
def deploy():
    upload()
    # restart()
