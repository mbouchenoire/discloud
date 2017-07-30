FROM python:3
ADD . /
RUN pip install -r requirements.txt
CMD [ "python", "./discloud/__init__.py" ]