FROM pytorch/pytorch:1.12.0-cuda11.3-cudnn8-runtime

RUN pip3 install pandas jupyterlab runnb

# Development only
COPY Makefile setup.cfg setup.py /tira-python-client/
COPY tira/ /tira-python-client/tira/
RUN pip3 install -e /tira-python-client
#
# RUN pip3 install tira==0.0.27

# Install custom requirements HERE

COPY template-notebook.ipynb /workspace/
COPY template-notebook-no-tira.ipynb /workspace/

ENV PYTHONPATH=/workspace

RUN jupyter trust /workspace/template-notebook.ipynb \
  jupyter trust /workspace/template-notebook-no-tira.ipynb
