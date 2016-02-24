FROM ubuntu:14.04

# http://askubuntu.com/a/190674
RUN echo debconf shared/accepted-oracle-license-v1-1 select true | debconf-set-selections
RUN echo debconf shared/accepted-oracle-license-v1-1 seen true | debconf-set-selections

# http://lifeonubuntu.com/ubuntu-missing-add-apt-repository-command/
RUN apt-get update && apt-get install -y python-pip python-dev python-numpy swig software-properties-common python-software-properties
RUN add-apt-repository ppa:webupd8team/java -y
# https://github.com/docker/docker/issues/4032
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y oracle-java8-installer oracle-java8-set-default 

RUN pip install --upgrade pip && pip install bllipparser nltk


COPY Dockerfile /camr/

COPY *.sh /camr/
COPY *.md /camr/

COPY *.py /camr/

COPY model.m.bz2 /camr/

COPY monthstats.json /camr/
COPY nationalities.json /camr/
COPY wiki.jsons /camr/

COPY common /camr/common
COPY feature /camr/feature
COPY lib /camr/lib
COPY resources /camr/resources
COPY rules /camr/rules
COPY scripts /camr/scripts
COPY stanfordnlp /camr/stanfordnlp
COPY temp /camr/temp
COPY bllip-parser /camr/bllip-parser

ENTRYPOINT ["/camr/containerized.sh"]
