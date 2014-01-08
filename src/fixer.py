#!/usr/bin/env python

import argparse
import calendar
import datetime
import logging
import sys
from xml.sax.saxutils import escape

import bs4
import dateutil.parser
from dateutil.tz import gettz


class SMS(object):
    """Class to encapsulate a single SMS message."""

    RECEIVED = 1
    SENT = 2
    XML_FORMAT = u"""<sms protocol="0" address="{address}" date="{date}" type="{type}" subject="null" body="{body}" toa="null" sc_toa="null" service_center="null" read="1" status="-1" locked="0" date_sent="0" readable_date="{readable_date}" contact_name="{contact_name}" />"""

    def __init__(self, raw_message, contact_name, address, timezone):
        if raw_message is None:
            raise

        self.contact_name = contact_name.strip()
        self.address = address.strip()

        if raw_message.find(class_='fn').text == contact_name:
            self.type = self.RECEIVED
        else:
            self.type = self.SENT

        self.body = escape(raw_message.find('q').text or '')
        self.body = self.body.replace("'", "&apos;")
        self.body = self.body.replace('"', "&quot;")
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
    """Parses arguments."""
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('input', type=argparse.FileType('r'), nargs='+',
                        help='input files')
    parser.add_argument('--output', type=argparse.FileType('w'), 
                        default=sys.stdout,
                        help='output filename')
    parser.add_argument('--timezone', type=str, default=None,
                        help='timezone (default: local)')
    parser.add_argument('--contacts', type=str, default=None,
                        help='contacts in case of missing numbers. example: '
                             '"First Last: +18885550123; Second Last: '
                             '+18005550123"')
    return parser.parse_args()


def get_names(soup):
    """Parses HTML file for contact names from the <title></title>."""
    title = soup.find('title').text
    if 'to' in title:
        return (name.strip() for name in title.split(' to'))
    else:
        return ("Me", title)


def parse_numbers(soup):
    """Returns list of tuples of names and numbers for each message in 
    the page.

    """
    # Parse names
    names = [e.text for e in soup.find_all(class_='fn')]

    # Parse numbers
    links = soup.find_all(class_='tel')
    hrefs = [link.get('href', '') for link in links]
    numbers = [href.lstrip("tel:") for href in hrefs]

    return zip(names, numbers)


def create_address_book(soups, address_book={}):
    """Parses all HTML files to create a 'default' address book in case 
    there is an HTML file where the contact did not reply and we cannot
    determine the contact's phone number."""
    for soup in soups:
        address_book.update(parse_numbers(soup))
    return address_book


def fix_sms(input=[], output=sys.stdout, timezone=None, logger=None,
            address_book={}):
    """Converts Google Voice HTML files to SMS Backup & Restore XML
    files.

    :param input: list of file objects for each input HTML conversation
    :param output: file object for XML file
    :param timezone: string for timezone (see Wikipedia for list)
    :param logger: logging object
    :param address_book: dict of name->numbers
    :return: contents of output, set of names missing phone numbers
    """
    logger.info("Parsing HTML.")
    soups = [bs4.BeautifulSoup(in_file.read()) for in_file in input]

    logger.info("Creating address book.")
    address_book = create_address_book(soups, address_book)
    
    all_messages = []
    missing = set()

    logger.info("Processing messages.")
    for soup in soups:
        if not soup.text:
            continue
        my_name, contact_name = get_names(soup)
        conversation_address_book = dict(parse_numbers(soup))
        if contact_name not in conversation_address_book:
            address = address_book.get(contact_name, '')
        else:
            address = conversation_address_book.get(contact_name)
        if not address:
            missing.add(contact_name)

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

    xml = [u"""<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<!--File Created By sms-fixer on {date}-->
<?xml-stylesheet type="text/xsl" href="sms.xsl"?>
<smses count="{count}">\n""".format(date=date, count=len(all_messages))]
    for message in all_messages:
        xml.append(u"  {message}\n".format(message=message.to_xml()))
    xml.append(u"</smses>")

    xml = u''.join(xml)
    output.write(xml.encode("utf-8"))
    logger.info('Done.')
    if missing:
        logger.warning(
            "Missing numbers (use --contacts): {0}".format(", ".join(missing)))
    return xml, missing


def main():
    """Main function called when run as main module."""
    logging.basicConfig()
    logger = logging.getLogger('fixer')
    logger.setLevel(logging.INFO)
    args = parse_args()

    strip = lambda t: tuple([e.strip() for e in t])
    contacts = dict([strip(l.split(':')) for l in args.contacts.split(';')
                                         if ':' in l])

    fix_sms(args.input, args.output, args.timezone, logger, contacts)


if __name__ == '__main__':
    main()

