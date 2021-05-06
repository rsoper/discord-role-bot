ARG arch=
FROM ${arch}python:3.8-slim-buster
WORKDIR /app
COPY ./bot /app
RUN pip3 install discord.py python-dotenv emoji flask

EXPOSE 5000

ENV DISCORD_TOKEN=

ENV CHANNEL_ID=

CMD [ "python3", "main.py" ]