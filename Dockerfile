FROM centos:6.8

# enable epel
RUN yum install -y epel-release

# install ansible
RUN yum install -y ansible

# setup environment
RUN mkdir -p /apps/thumbor/builds/working-copy
WORKDIR /apps/thumbor/builds/current

# copy all the code
COPY . /apps/thumbor/builds/current

# deploy app using ansible
RUN echo -e "[thumbor_vagrant]\nlocalhost ansible_connection=local docker=true" > .playbooks/hosts
RUN ansible-playbook -i .playbooks/hosts .playbooks/deploy_thumbor.yml --skip-tags deploy

# setup supervisor to run and monitor multiple daemons
RUN echo "[supervisord]" > /etc/supervisord.conf && \
    echo "nodaemon=true" >> /etc/supervisord.conf && \
    echo "" >> /etc/supervisord.conf && \
    echo "[program:nginx]" >> /etc/supervisord.conf && \
    echo "command=/usr/sbin/nginx -c /etc/nginx/nginx.conf -g 'daemon off;'" >> /etc/supervisord.conf && \
    echo "" >> /etc/supervisord.conf && \
    echo "[include]" >> /etc/supervisord.conf && \
    echo "files = /etc/supervisor.d/thumbor.ini" >> /etc/supervisord.conf

# run supervisor
CMD ["/usr/bin/supervisord"]
