FROM pytorch/pytorch:1.12.0-cuda11.3-cudnn8-runtime

RUN pip3 install pandas jupyterlab runnb tira==0.0.28

COPY template-notebook.ipynb template-notebook-no-tira.ipynb /workspace/

ENV PYTHONPATH=/workspace

RUN jupyter trust /workspace/template-notebook.ipynb \
  jupyter trust /workspace/template-notebook-no-tira.ipynb
