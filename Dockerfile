FROM python:3.12
EXPOSE 5000
VOLUME /data
WORKDIR /usr/src/app
COPY app/. .
RUN pip install --no-cache-dir --upgrade -r requirements/requirements.txt
# RUN pip3 install --no-cache-dir -r requirements/requirements-pi.txt
ENTRYPOINT [ "./hompi" ]