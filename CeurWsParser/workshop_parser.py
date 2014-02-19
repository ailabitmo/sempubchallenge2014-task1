import re

from grab.tools import rex
from datetime import datetime
from items import Workshop


def parse_workshop_summary(obj):
    href = obj[0].find('.//td[last()]//a[@href]')
    summary = obj[1].find('.//td[last()]').text_content()
    title = rex.rex(summary, r'(.*)Edited\s*by.*', re.I | re.S).group(1)
    volume_number = rex.rex(href.get('href'), r'.*http://ceur-ws.org/Vol-(\d+).*').group(1)

    workshop = Workshop(volume_number)
    workshop.label = href.text
    workshop.url = href.get('href')

    time_match_1 = rex.rex(title, r'.*,\s*([a-zA-Z]+)[,\s]*(\d{1,2})[\w\s]*,\s*(\d{4})', re.I,
                           default=None)
    time_match_2 = rex.rex(title, r'.*,\s*([a-zA-Z]+)[,\s]*(\d{1,2})[\w\s]*-\s*(\d{1,2})[\w\s,]*(\d{4})', re.I,
                           default=None)
    time_match_3 = rex.rex(title, r'.*,\s*([a-zA-Z]+)\s*(\d+)\s*-\s*([a-zA-Z]+)\s*(\d+)\s*,\s*(\d{4})', re.I,
                           default=None)
    if time_match_1:
        try:
            workshop.time = datetime.strptime(
                time_match_1.group(1) + "-" + time_match_1.group(2) + "-" + time_match_1.group(3), '%B-%d-%Y')
        except:
            pass
    elif time_match_2:
        try:
            workshop.time = [
                datetime.strptime(time_match_2.group(1) + "-" + time_match_2.group(2) + "-" + time_match_2.group(4),
                                  '%B-%d-%Y'),
                datetime.strptime(time_match_2.group(1) + "-" + time_match_2.group(3) + "-" + time_match_2.group(4),
                                  '%B-%d-%Y')
            ]
        except:
            pass
    elif time_match_3:
        try:
            workshop.time = [
                datetime.strptime(time_match_3.group(1) + "-" + time_match_3.group(2) + "-" + time_match_3.group(5),
                                  '%B-%d-%Y'),
                datetime.strptime(time_match_3.group(3) + "-" + time_match_3.group(4) + "-" + time_match_3.group(5),
                                  '%B-%d-%Y')
            ]
        except:
            pass
    else:
        #There is no event time information
        pass

    return workshop