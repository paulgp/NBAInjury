#python3


import layoutparser as lp

import matplotlib.pyplot as plt
import itertools
import pandas as pd
import numpy as np
import cv2
import csv
import urllib.request
import shutil
from pdf2image import convert_from_path
from io import BytesIO
from PIL import Image

PATH = "https://ak-static.cms.nba.com/referee/injury/"
RAW_OUTPUT_PATH = "../data/raw/"
CLEAN_OUTPUT_PATH = "../data/parsed/"


def pull_pdf(url, file_name):
    with urllib.request.urlopen(url) as response, open(file_name, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
    return response

def parse_pdf(file_name, ocr_agent):
    pages=convert_from_path(file_name)
    full_data = []
    i = 0
    for page in pages:
        fnout = RAW_OUTPUT_PATH + 'page' + str(i) + '.jpg'
        page.save(fnout, 'JPEG')
        image = cv2.imread(fnout)
        res = ocr_agent.detect(image, return_response=True)

        layout = ocr_agent.gather_full_text_annotation(res, agg_level=lp.GCVFeatureType.WORD)
        team_names = layout.filter_by(
            lp.Rectangle(x_1=658, y_1=200, x_2=997, y_2=1537)
        )
        player_names = layout.filter_by(
            lp.Rectangle(x_1=1000, y_1=200, x_2=1367, y_2=1537),
        )
        status =  layout.filter_by(
            lp.Rectangle(x_1=1369, y_1=200, x_2=1644, y_2=1537),
        )
        reason =  layout.filter_by(
            lp.Rectangle(x_1=1670, y_1=200, x_2=1970, y_2=1537),
        )

        y_0 = 200
        height = 50
        y_1 = 1540

        data = []
        old_team = []
        for y in range(y_0, y_1, height):
            interval = lp.Interval(y,y+height, axis='y')
            team = team_names.\
                filter_by(interval).\
                get_texts()
            if team == []:
                team = old_team
            old_team = team

            player = player_names.\
                filter_by(interval).\
                get_texts()

            stat = status.\
                filter_by(interval).\
                get_texts()

            reas = reason.\
                filter_by(interval).\
                get_texts()
            if player != []:
                data.append([''.join(team), ''.join(player),
                             ''.join(stat), ''.join(reas)])

        full_data.append([i,data])
        i = i+1
    return full_data


### Load up OCR
#### REPLACE THIS WITH YOUR GOOGLE VISION KEY
#### See this for details: https://cloud.google.com/vision/docs/quickstart-client-libraries
#### See details on layout parser here: https://layout-parser.readthedocs.io/en/latest/example/parse_ocr/index.html

clientid = 'basketballvision-311620-0ac76e61bf8a.json'
ocr_agent = lp.GCVAgent.with_credential(clientid, languages = ['en'])


for year,month,day in itertools.product([2021],[4],[1]):

    fn = "Injury-Report_%d-%s-%s_08PM.pdf" % (year, str(month).rjust(2,'0'), str(day).rjust(2,'0'))
    url = PATH + fn
    file_name = RAW_OUTPUT_PATH + fn
    ### Download file    
    try:
        pull_pdf(url, file_name)
    except urllib.request.HTTPError:
       print("No Injury report on %d-%d-%d" % (year, month, day))

    ## Parse Files
    full_data = parse_pdf(file_name, ocr_agent)
    with open(CLEAN_OUTPUT_PATH + fn[:-4]+".csv", 'w') as f:
        writer = csv.writer(f)
        writer.writerow(["team", "player", "status", "reason"])
        for line in full_data:
            for line2 in line[1]:
                writer.writerow(line2)
