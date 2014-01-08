#!/usr/bin/env python

import argparse
import calendar
import datetime
import logging
import sys

import bs4
import dateutil.parser
from dateutil.tz import gettz


class SMS(object):

    RECEIVED = 1
    SENT = 2
    XML_FORMAT = """<sms protocol="0" address="{address}" date="{date}" type="{type}" subject="null" body="{body}" toa="null" sc_toa="null" service_center="null" read="1" status="-1" locked="0" date_sent="0" readable_date="{readable_date}" contact_name="{contact_name}" />"""

    def __init__(self, raw_message, contact_name, address, timezone):
        if raw_message is None:
            raise

        self.contact_name = contact_name
        self.address = address

        if raw_message.find(class_='fn').text == contact_name:
            self.type = self.RECEIVED
        else:
            self.type = self.SENT

        self.body = raw_message.find('q').text or ''
        raw_date = raw_message.find(class_='dt').get('title', '')
        self.utc_date = dateutil.parser.parse(raw_date)

        unix_timestamp = calendar.timegm(self.utc_date.utctimetuple())
        milliseconds = self.utc_date.microsecond / 1000
        self.date = "%s%s" % (unix_timestamp, milliseconds)

        self.localized_date = self.utc_date.astimezone(gettz(timezone))

        modified_date = self.localized_date.strftime('%b %d, %Y %I:%M:%S %p')
        self.readable_date = modified_date.replace(" 0", " ")

    def to_xml(self):
        """Converts object to XML string using attribute values."""
        return self.XML_FORMAT.format(**self.__dict__)


    def __repr__(self):
        return "{0} {1} [{2}]: {3}".format(
            "to" if self.type == self.SENT else "from",
            self.contact_name,
            self.readable_date,
            self.body)


def parse_args():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('input', type=argparse.FileType('r'), nargs='+',
                        help='input files')
    parser.add_argument('--output', type=argparse.FileType('w'), 
                        default=sys.stdout,
                        help='output filename')
    parser.add_argument('--timezone', type=str, default=None,
                        help='timezone (default: local)')
    return parser.parse_args()


def get_names(soup):
    return (name.strip() for name in soup.find('title').text.split('to'))


def parse_numbers(soup):
    # Parse names
    names = [e.text for e in soup.find_all(class_='fn')]

    # Parse numbers
    links = soup.find_all(class_='tel')
    hrefs = [link.get('href', '') for link in links]
    numbers = [href.lstrip("tel:") for href in hrefs]

    return zip(names, numbers)


def create_address_book(soups):
    address_book = {}
    for soup in soups:
        # Update address book
        address_book.update(parse_numbers(soup))
    return address_book


def fix_sms(input=[], output=sys.stdout, timezone=None, logger=None):
    """Converts Google Voice HTML files to SMS Backup & Restore XML
    files.

    :param input: list of file objects for each input HTML conversation
    :param output: file object for XML file
    :param timezone: string for timezone (see Wikipedia for list)
    :param logger: logging object
    :return: contents of output
    """
    logger.info("Parsing HTML.")
    soups = [bs4.BeautifulSoup(in_file.read()) for in_file in input]

    logger.info("Creating address book.")
    address_book = create_address_book(soups)
    all_messages = []

    logger.info("Processing messages.")
    for soup in soups:
        my_name, contact_name = get_names(soup)
        # address = address_book.get(contact_name, '')
        conversation_address_book = dict(parse_numbers(soup))
        print conversation_address_book
        if contact_name not in conversation_address_book:

            address = address_book.get(contact_name, '')
        else:
            address = conversation_address_book.get(contact_name)

        raw_messages = soup.find_all(class_="message")
        messages = map(lambda m: SMS(m, contact_name, address, timezone), 
                       raw_messages)
        all_messages += messages

    num_contacts = max(0, len(address_book.keys()) - 1)  # don't count me
    logger.info("Processed {0} messages for {1} contact{2}.".format(
        len(all_messages), num_contacts, 's' if num_contacts != 1 else ''))  

    if hasattr(output, 'name'):
        filename = output.name
    else:
        filename = "<unknown file>"
    logger.info("Outputing XML to {0}".format(filename))
    date = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    xml = ""
    xml += ("""<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<!--File Created By sms-fixer on {date}-->
<?xml-stylesheet type="text/xsl" href="sms.xsl"?>
<smses count="{count}">\n""".format(date=date, count=len(all_messages)))
    for message in all_messages:
        xml += "  {message}\n".format(message=message.to_xml())
    xml += "</smses>"
    output.write(xml)
    logger.info('Done.')
    return xml


def main():
    logging.basicConfig()
    logger = logging.getLogger('fixer')
    logger.setLevel(logging.INFO)
    args = parse_args()

    fix_sms(args.input, args.output, args.timezone, logger)


if __name__ == '__main__':
    main()

