FROM python:3.12
ARG TARGET
EXPOSE 5000
VOLUME /data
WORKDIR /usr/src/app
COPY app/. .
RUN pip install --no-cache-dir --upgrade -r requirements/requirements.txt
RUN if [ "$TARGET" = "PI" ]; then \
      pip install --no-cache-dir -r requirements/requirements-pi.txt; \
    fi
ENTRYPOINT [ "./hompi" ]