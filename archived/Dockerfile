# FROM Dockerfile_debian_20240506_fixed  # not sure if this would be the correct name for it
# MAINTAINER Wenjing Ma mawenjing1993@gmail.com

# ADD . /app
COPY ./requirements.txt /BARTweb/requirements.txt
# RUN pip install uwsgi
RUN pip3 install --break-system-packages -r /BARTweb/requirements.txt

# Copy over the apache configuration file and enable the site
COPY ./apache-flask.conf /etc/apache2/sites-available/apache-flask.conf
RUN a2ensite apache-flask
RUN a2enmod headers

RUN mkdir -p /BARTweb
COPY . /BARTweb/

# feed apache to docker
RUN a2dissite 000-default.conf
RUN a2ensite apache-flask.conf

EXPOSE 80

# ENV HOME /app change to apache-flask
WORKDIR /BARTweb/

# For log -> in 20230401j docker image
RUN mkdir /log && touch /log/bartweb.log
RUN chown -R www-data:www-data /log
# original For log
RUN mkdir -p usercase/log
RUN touch usercase/log/bartweb.log
RUN chown -R www-data:www-data usercase/log
RUN chmod -R 775 usercase/log

#run apache, this directory is present with installation of apache
CMD ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]
