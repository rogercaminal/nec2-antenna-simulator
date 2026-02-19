# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /opt

# System deps needed to build necpp/PyNEC + run git builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    git \
    swig \
    autoconf \
    automake \
    libtool \
    pkg-config \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Python deps for notebooks + typical antenna work
RUN pip install --no-cache-dir \
    notebook \
    jupyterlab \
    numpy \
    scipy \
    matplotlib \
    plotly \
    ipympl \
    ipywidgets \
    jupyterlab_widgets

# Clone and build python-necpp (necpp + PyNEC)
RUN git clone --recursive https://github.com/tmolteno/python-necpp.git \
 && cd python-necpp \
 && git submodule update --init --recursive

# Build/install necpp first (C wrapper)
RUN cd /opt/python-necpp/necpp \
 && sed -i 's/swig3\.0/swig/g' build.sh || true \
 && chmod +x build.sh \
 && ./build.sh \
 && pip install --no-cache-dir -v .

# Build/install PyNEC (C++ wrapper)
RUN cd /opt/python-necpp/PyNEC \
 && chmod +x build.sh \
 && ./build.sh \
 && pip install --no-cache-dir -v .

# Quick import test at build time (fails the build if broken)
RUN python -c "import PyNEC; from PyNEC import nec_context; print('PyNEC OK:', PyNEC.__file__)"

# Create a place for your code
WORKDIR /work

# (Optional) install your package in editable mode if it exists
# We’ll rely on docker-compose mounting it into /work/nec2_antenna_simulator
RUN pip install --no-cache-dir -e /work/nec2_antenna_simulator || true

EXPOSE 8888

# Jupyter: bind on all interfaces, no browser, allow running as root in container
CMD ["jupyter", "lab", \
     "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", \
     "--NotebookApp.token=", "--NotebookApp.password="]

