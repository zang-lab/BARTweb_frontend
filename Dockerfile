FROM debian:latest
MAINTAINER Yifan Zhang

# Update OS
RUN apt-get update -y

# Install Python other things
#RUN apt-get install -y python-pip python-dev build-essential
RUN apt-get update && apt-get install -y apache2 \
    libapache2-mod-wsgi-py3 \
    build-essential \
    python3 \
    python3-dev\
    python3-pip \
    vim \
 && apt-get clean \
 && apt-get autoremove \
 && rm -rf /var/lib/apt/lists/*

# && do not continue if any fails


# ADD . /app
COPY ./requirements.txt /BARTweb/requirements.txt
# RUN pip install uwsgi
RUN pip3 install -r /BARTweb/requirements.txt

# Copy over the apache configuration file and enable the site
COPY ./apache-flask.conf /etc/apache2/sites-available/apache-flask.conf
RUN a2ensite apache-flask
RUN a2enmod headers

COPY  . /BARTweb/

RUN a2dissite 000-default.conf
RUN a2ensite apache-flask.conf

EXPOSE 80

# ENV HOME /app change to apache-flask
WORKDIR /BARTweb/

# For log
RUN mkdir -p log
RUN touch log/bartweb.log
RUN chown -R www-data:www-data log
RUN chmod -R 775 log

CMD /usr/sbin/apache2ctl -D FOREGROUND

