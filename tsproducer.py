import json

from kafka import KafkaProducer


def send_msg(host, recv, msg):
    producer = KafkaProducer(bootstrap_servers=host, api_version=(0, 9))
    producer.send(recv, json.dumps(msg).encode())
    producer.close()

info = {
    'id': None,
    'language': 'Java',
    'description': 'wori',
}
msg = {
    'url':'https://github.com/valysin/valysin',
    'info':info,
    'url_type':'github',
    'branch':'master',
    'username':None,
    'password':None,
    'is_private':False

}
send_msg('10.141.221.85:9092', 'DuplicateRepo', msg)