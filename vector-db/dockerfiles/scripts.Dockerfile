FROM python:3.12.3

RUN apt-get update &&  \
    apt-get install --no-install-recommends tesseract-ocr poppler-utils ffmpeg libsm6 libxext6 -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir -U pip

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -U -r /tmp/requirements.txt

COPY scripts/*.py /
