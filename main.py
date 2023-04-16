# -*- coding: utf-8 -*-
import argparse
import csv
import logging
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

os.environ['PYWIKIBOT_DIR'] = os.path.dirname(os.path.realpath(__file__))
import pywikibot


class BlockTanet:
    EXPIRY = '1 year'
    ANONONLY = True
    NOCREATE = True
    NOEMAIL = False
    ALLOWUSERTALK = True
    REBLOCK = False

    def __init__(self, args):
        self.args = args

        self.site = pywikibot.Site()
        self.site.login()

        self.logger = logging.getLogger('archive_ar')
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        self.logger.addHandler(stdout_handler)

    def get_school(self, ip):
        content = requests.get('https://whois.tanet.edu.tw/showWhoisPublic.php?queryString={}'.format(ip)).text
        bs4 = BeautifulSoup(content, 'html.parser')
        table = bs4.find_all('table')[1]
        school = ''
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) == 2 and tds[0].text == 'Chinese Name':
                school = tds[1].text
        return school

    def block(self, ip_long):
        ip_short = re.sub(r'/\d+$', '', ip_long)
        school = self.get_school(ip_short)
        reason = '{{School block}}'
        if school:
            reason += '<!-- ' + school + ' -->'

        save = True
        if self.args.confirm:
            save = pywikibot.input_yn('Block {} with reason {} ?'.format(ip_long, reason), 'Y')
        else:
            self.logger.debug('Block {} with reason {}'.format(ip_long, reason))

        if save:
            self.logger.debug('blocking')
            try:
                user = pywikibot.User(self.site, ip_long)
                result = self.site.blockuser(
                    user=user,
                    expiry=self.EXPIRY,
                    reason=reason,
                    anononly=self.ANONONLY,
                    nocreate=self.NOCREATE,
                    noemail=self.NOEMAIL,
                    allowusertalk=self.ALLOWUSERTALK,
                    reblock=self.REBLOCK,
                )
                self.logger.info('block {} result: {}'.format(ip_long, result))
            except Exception as e:
                self.logger.error('error when block {}: {}'.format(ip_long, e))
        else:
            self.logger.debug('skip')

    def batch(self):
        with open(self.args.file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                self.block(row[0])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--confirm', action='store_true')
    parser.add_argument('-d', '--debug', action='store_const', dest='loglevel', const=logging.DEBUG, default=logging.INFO)
    parser.add_argument('--ip', help='ip to block')
    parser.add_argument('--file', help='file contains ip to block')
    args = parser.parse_args()

    block_tanet = BlockTanet(args)
    block_tanet.logger.setLevel(args.loglevel)
    block_tanet.logger.debug('args: %s', args)
    if args.ip:
        block_tanet.block(args.ip)
    elif args.file:
        block_tanet.batch()
    else:
        parser.print_help()
