from fabric.api import *

env.user = 'harlan'
env.hosts = ['harlanhaskins.com']

domain = 'harlanhaskins.com'
subdom = 'www'

def push():
    local('jekyll build')
    local('zip -r _site _site')
    run('rm -f /var/www/%s/_site.zip' % (domain))
    run('rm -rf /var/www/%s/_site' % (domain))
    put('_site.zip', '/var/www/%s/_site.zip' % (domain))
    local("rm -rf _site")
    local("rm _site.zip")
    run('unzip /var/www/%s/_site.zip -d /var/www/%s' % (domain, domain))
    run('rm -rf /var/www/%s/%s' % (domain, subdom))
    run('mv /var/www/%s/_site /var/www/%s/%s' % (domain, domain, subdom))
