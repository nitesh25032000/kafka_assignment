import argparse
import pandas as pd
from confluent_kafka import Consumer
from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONDeserializer
import os

API_KEY = '36FGH6GXBPQ46YJN'
ENDPOINT_SCHEMA_URL  = 'https://psrc-e8157.us-east-2.aws.confluent.cloud'
API_SECRET_KEY = 'jTB4sNsLxNGPsryfQ1Wnsf/i7izgwBS11hsmUiVjXtNuUD+p2kfDt7cqY8raJpEO'
BOOTSTRAP_SERVER = 'pkc-ymrq7.us-east-2.aws.confluent.cloud:9092'
SECURITY_PROTOCOL = 'SASL_SSL'
SSL_MACHENISM = 'PLAIN'
SCHEMA_REGISTRY_API_KEY = 'NYFXW3PCGTXLBZMZ'
SCHEMA_REGISTRY_API_SECRET = 'Cm0DbpeRRHbSyB9YwktY0rhy+tfQ/yWT8jHdnrvvwq4mWQqjQThrfOknqyZue6Zv'



FILE_PATH = "C:/Users/NITESH/Downloads/output1.csv"


def sasl_conf():
    sasl_conf = {'sasl.mechanism': SSL_MACHENISM,
                 # Set to SASL_SSL to enable TLS support.
                 #  'security.protocol': 'SASL_PLAINTEXT'}
                 'bootstrap.servers': BOOTSTRAP_SERVER,
                 'security.protocol': SECURITY_PROTOCOL,
                 'sasl.username': API_KEY,
                 'sasl.password': API_SECRET_KEY
                 }
    return sasl_conf


def schema_config():
    return {'url': ENDPOINT_SCHEMA_URL,

            'basic.auth.user.info': f"{SCHEMA_REGISTRY_API_KEY}:{SCHEMA_REGISTRY_API_SECRET}"

            }


class Restaurant:
    def __init__(self, record: dict):
        for k, v in record.items():
            setattr(self, k, v)

        self.record = record

    @staticmethod
    def dict_to_restaurant(data: dict, ctx):
        return Restaurant(record=data)

    def __str__(self):
        return f"{self.record}"


def main(topic):
    schema_registry_conf = schema_config()
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)
    schema_str = schema_registry_client.get_latest_version('restaurent-take-away-data-value').schema.schema_str
    json_deserializer = JSONDeserializer(schema_str,
                                         from_dict=Restaurant.dict_to_restaurant)

    consumer_conf = sasl_conf()
    consumer_conf.update({
        'group.id': 'group1',
        'auto.offset.reset': "earliest"})

    consumer = Consumer(consumer_conf)
    consumer.subscribe([topic])
    messages = []
    while True:
        try:
            # SIGINT can't be handled when polling, limit timeout to 1 second.
            msg = consumer.poll(1.0)
            if msg is None:
                if len(messages) != 0:
                    df = pd.DataFrame.from_records(messages)
                    if not os.path.isfile(FILE_PATH):
                        df.to_csv(FILE_PATH, index=False)
                    else:
                        df.to_csv(FILE_PATH, mode='a', header=False, index=False)
                    messages = []
                continue
            restaurant = json_deserializer(msg.value(), SerializationContext(msg.topic(), MessageField.VALUE))

            if restaurant is not None:
                print("User record {}: restaurant: {}\n"
                      .format(msg.key(), restaurant))
                messages.append(restaurant.record)

        except KeyboardInterrupt:
            break

    consumer.close()


main("restaurent-take-away-data")
