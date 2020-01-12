import argparse
import json
import logging
import os.path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from vendor import registry
from inventory import Base, Device

__all__ = ['Config', "HomeNetChecker', 'RegisterCommand"]

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(title='subcommands', help='Operations to be performed')

logger = logging.getLogger()
registry.load_vendors()

class Config:
    dsn = 'sqlite:///inv.db'
    log_level = logging.INFO
    log_file = None

    def __init__(self, config_fp):
        if config_fp:
            self.load(config_fp)

    def load(self, fp):
        config = json.load(fp)
        if 'dsn' in config:
            self.dsn = config.dsn
        if 'log' in config:
            if 'level' in config['log']:
                self.log_level = config['log']['level'].upper()
            if 'file' in config['log']:
                self.log_file = config['log']['file']

class RegisterCommand:
    def __init__(self, command, description, args = []):
        self.command = command
        self.description = description
        self.args_list = args

    def __call__(self, method):
        parser_command = subparsers.add_parser(self.command, description=self.description)
        for args in self.args_list:
            name = args.pop('name')
            parser_command.add_argument(name, **args)
        parser_command.set_defaults(func=method)

        return method

class HomeNetChecker():
    def __init__(self, config):
        self.config = config
        self.session = self._get_db()
        logger.debug('Loaded vendors: %d', len(registry.items()))

    def _get_db(self):
        engine = create_engine(self.config.dsn)
        Session = sessionmaker(bind=engine)
        return Session()

    @RegisterCommand('initialize-db', 'Create database table structure')
    def init_db(self, args):
        engine = self.session.get_bind()
        Base.metadata.create_all(engine)
        logger.info('Tables created')

    @RegisterCommand('query', 'Check for available device updates')
    def query(self, args):
        for instance in self.session.query(Device).order_by(Device.id):
            logger.info(instance.name, instance.vendor)

    @RegisterCommand('vendor-list', 'Print list of supported vendors')
    def vendor_list(self, args):
        #width = max([len(vendor_id) for vendor_id in registry.keys()])
        print('%s\t%s' % ('Vendor ID', 'Name'))
        for vendor_id, vendor_class in registry.items():
            vendor = vendor_class()
            print('%s\t%s' % (vendor_id, vendor.name()))

    @RegisterCommand('add-device', 'Add a device to be checked', [
        {'name': '--vendor-id', 'choices': registry.keys(), 'help': 'Vendor ID', 'required': True},
        {'name': '--model', 'help': 'Model ID', 'required': True},
        {'name': '--version', 'help': 'Device version'},
        {'name': '--description', 'help': 'Description'}])
    def add_item(self, args):
        keys = [c.name for c in Device.__mapper__.columns if c.name != 'id']
        values = vars(args)
        device = Device(**{k: values[k] for k in keys})
        self.session.add(device)
        self.session.commit()
        logger.info('Device added with id %d', device.id)


def homenet():
    parser.add_argument('--config', '-c', type=argparse.FileType('r'),
        help='Path to configuration file')
    args = parser.parse_args()
    config = Config(args.config)
    log_config = {'level': config.log_level}
    if config.log_file:
        log_config['filename'] = config.log_file,
        log_config['filemode'] = 'a'
    logging.basicConfig(**log_config)
    checker = HomeNetChecker(config)
    args.func(checker, args)

if __name__ == '__main__':
    homenet()