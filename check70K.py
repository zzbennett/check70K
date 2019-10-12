import requests
from bs4 import BeautifulSoup
import sys
import json
import boto3
import botocore


ARTISTS_URL = 'http://70000tons.com/artists/'
BUCKET_NAME = '70k'  # replace with your bucket name
KEY = '70Kbands.txt'  # replace with your object key

conf = json.loads(open("./config.json").read())
phone_numbers = conf["phone_numbers"]
slack_endpoint = conf["slack_endpoint"]
aws_access_key = conf["aws_access_key"]
aws_secret_key = conf["aws_secret_key"]

sns = boto3.client('sns', region_name="us-east-1", aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)
s3 = boto3.resource('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)


def handler(event,context):
    page = requests.get(ARTISTS_URL).text
    soup = BeautifulSoup(page, 'html.parser')
    band_blocks = soup.find_all('div', attrs={'class': 'ib-block'})
    bands = []
    for band_block in band_blocks:
        bands.append(band_block.find("img").get("title"))
    
    # compare the band list to the file in s3 that was written by the last run
    s3.Bucket(BUCKET_NAME).download_file(KEY, "/tmp/"+KEY)
    previous_bands = open("/tmp/"+KEY).read()
    
    bands_list = bands
    bands_list = [band.strip('\n') for band in bands_list]
    bands_list = [band.strip(' ') for band in bands_list]
    
    previous_bands_list = previous_bands.split(",")
    previous_bands_list = [band.strip('\n') for band in previous_bands_list]
    previous_bands_list = [band.strip(' ') for band in previous_bands_list]
    previous_bands_list = [band for band in previous_bands_list if band != '']

    print("Current band list: " + str(bands_list))
    print("Previous band list: " + str(previous_bands_list))

    if bands_list != previous_bands_list:
        new_bands = set(bands_list) - set(previous_bands_list)
        message = "Found new bands!!!! New bands are "+", ".join(new_bands)
        print(message)
        for phone_number in phone_numbers:
            sns.publish(PhoneNumber=phone_number, Message=message)
        print(requests.post(url=slack_endpoint, json={'text': message}).text)
    
    # overwrite the old file in s3
    print("Overwriting previous bands with current bands in S3")
    output = ",".join(bands) if len(bands) > 0 else ''
    print(output)
    f = open("/tmp/"+KEY, 'w+')
    f.write(output)
    f.flush()
    f.close()

    print("Writing contexts to file " + BUCKET_NAME + "/" + KEY + ": " + open("/tmp/" + KEY).read())

    s3.Bucket(BUCKET_NAME).upload_file("/tmp/"+KEY, KEY)


if __name__ == '__main__':
    handler(None, None)
