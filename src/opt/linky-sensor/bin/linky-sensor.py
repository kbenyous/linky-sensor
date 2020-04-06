#!/opt/linky-sensor/virtualenv/bin/python3
# -*- coding: UTF-8 -*-

import serial
import logging
import subprocess
import io
import datetime
import configparser
import paho.mqtt.client as mqtt
import sdnotify
import json

# Port serial
stty_port = '/dev/serial0'

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


def read_frame(ser, greedy_mode=False):
    logging.info('read_frame()')

    buffer = bytearray()
    frame_start = 0x02
    frame_end = 0x03

    framestart_idx = 0
    frameend_idx = 0

    while True:
        # Recherche le caractère de début de trame,
        # Etend le buffer si nécessaire en lisant depuis le stream
        while frame_start not in buffer:
            extend_size = max(1, min(2048, ser.in_waiting)
                              ) if greedy_mode else 2048
            logging.info(
                "read_frame : searching frame start, buffer extend_size: %s" % extend_size)
            extend_data = ser.read(extend_size)
            buffer.extend(extend_data)
        framestart_idx = buffer.find(frame_start)

        # Recherche le caractère de fin de trame,
        # Etend le buffer si nécessaire en lisant depuis le stream
        while -1 == buffer.find(frame_end, framestart_idx+1):
            extend_size = max(1, min(2048, ser.in_waiting)
                              ) if greedy_mode else 2048
            logging.info(
                "read_frame : searching frame end, buffer extend_size: %s" % extend_size)
            extend_data = ser.read(extend_size)
            buffer.extend(extend_data)
        frameend_idx = buffer.find(frame_end, framestart_idx+1)

        logging.info("read_frame : Frame found in buffer[%i:%i]" % (
            framestart_idx, frameend_idx+1))
        frame = buffer[framestart_idx:frameend_idx+1]
        buffer = buffer[frameend_idx+1:]
        yield frame


def read_data(frame):

    frame_buffer = bytearray(frame[1:-1])
    result = dict()
    #data_start = b'\n'
    data_end = b'\r'
    data_separator = b'\t'

    for data_line in frame_buffer.split(sep=data_end):
        # Le caractère de fin de ligne est enlevé par le split,
        # Mais il reste le caractère de debut de ligne
        data_line = data_line[1:]

        data_items = data_line.split(data_separator)

        label = data_items[0].decode('ascii')
        checksum = None
        donnee = None
        horodate = None

        if len(data_items) == 3:
            donnee = data_items[1].decode('ascii')
            checksum = data_items[2][0]
        if len(data_items) == 4:
            horodate = data_items[1].decode('ascii')
            donnee = data_items[2].decode('ascii')
            checksum = data_items[3][0]

        computed_checskum = (sum(data_line[0:-1]) & 0x3F) + 0x20

        if(computed_checskum == checksum):
            if horodate is not None:
                try:
                    timestamp = decode_horodate(horodate)
                except ValueError:
                    timestamp = 0
                result[label] = {'Value': donnee,
                                 'Timestamp': timestamp.isoformat()}
            else:
                result[label] = {'Value': donnee}

    return result


def decode_horodate(horodate):
    # Enleve le premier caractère qui ne sert pars à la compréhension de la date
    buff = horodate[1:]
    logging.info(buff)
    result_datetime = datetime.datetime.strptime(buff, '%y%m%d%H%M%S')
    return result_datetime


def main():

    # Notifications pour SystemD
    systemd_notifier = sdnotify.SystemdNotifier()

    # Lecture de la conf
    config = configparser.RawConfigParser()
    config.read('/etc/linky-sensor/linky-sensor.cfg')
    systemd_notifier.notify('RELOADING=1')
    
    # Configuration du client mqtt
    mqtt_broker_hostname = config.get('mqtt_broker', 'hostname',fallback='localhost')
    mqtt_broker_port = config.getint('mqtt_broker', 'port', fallback=1883)
    mqtt_client_name = config.get('mqtt_broker', 'client_name', fallback='Linky-Sensor')

    # Configuration du client mqtt
    client = mqtt.Client(mqtt_client_name)
    client.connect_async(mqtt_broker_hostname, mqtt_broker_port)

    # Reconfigure le port serial pour eviter
    # l'erreur: termios.error: (22, 'Invalid argument')
    logging.info('Reconfigure stty %s' % stty_port)
    subprocess.call(['stty', '-F',  stty_port, 'iexten'])

    systemd_notifier.notify('READY=1')
    
    client.loop_start()

    poll_tty_every = 0.25
    watchdog_every = 15
    
    with serial.Serial(port=stty_port, baudrate=9600, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE,
                       bytesize=serial.SEVENBITS, timeout=poll_tty_every) as ser:
        logging.info('Start reading frames')
        frame_count = 0
        for frame in read_frame(ser):

            client.publish('house/sensors/energy',json.dumps(frame))

            # Notification régulière à SystemD pour la surveillance du démon
            frame_count += 1
            if frame_count > watchdog_every:
                systemd_notifier.notify('WATCHDOG=1')
                frame_count = 0

if __name__ == '__main__':
    main()
