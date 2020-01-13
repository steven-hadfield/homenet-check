import argparse
import json
import logging
import os.path

from tempfile import gettempdir

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tabulate import tabulate

from vendor import registry
from inventory import Base, Device

__all__ = ['Config', "HomeNetChecker', 'RegisterCommand"]

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(title='subcommands', help='Operations to be performed')

logger = logging.getLogger('homenet')
registry.load_vendors()

# TODO: Move classes to separate file?
# TODO: Split commands?
# TODO: Add tests

class Config:
    dsn = 'sqlite:///inv.db'
    log_level = logging.INFO
    log_file = None
    cache_dir = None

    def __init__(self, config_fp):
        if config_fp:
            self.load(config_fp)
        if self.cache_dir is None:
            self.cache_dir = gettempdir()

    def load(self, fp):
        config = json.load(fp)
        if 'dsn' in config:
            self.dsn = config.dsn
        if 'log' in config:
            if 'level' in config['log']:
                self.log_level = config['log']['level'].upper()
            if 'file' in config['log']:
                self.log_file = config['log']['file']
        if 'cache' in config:
            self.cache_dir = config['cache']


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

def non_empty_argument(arg):
    if arg is not None and arg.strip() == '':
        raise argparse.ArgumentTypeError('Value cannot be an empty string')
    return arg

class HomeNetChecker():
    def __init__(self, config):
        self.config = config
        self.session = self._get_db()
        logger.debug('Loaded vendors: %d', len(registry.keys()))

    def _get_db(self):
        engine = create_engine(self.config.dsn)
        Session = sessionmaker(bind=engine)
        return Session()

    @RegisterCommand('initialize-db', 'Create database table structure')
    def init_db(self, args):
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config('alembic.ini')
        alembic_cfg.set_main_option("sqlalchemy.url", self.config.dsn)
        engine = self.session.get_bind()
        if not engine.dialect.has_table(engine, 'devices'):
            Base.metadata.create_all(engine)
            logger.info('Tables created')

            command.stamp(alembic_cfg, "head")
            # TODO: Fix alembic overriding root log
            logger.debug('Alembic history recorded')
        else:
            logger.info('Checking for database changes')
            command.upgrade(alembic_cfg, "head")
            logger.debug('Alembic upgrade completed (if any)')

    @RegisterCommand('query', 'Check for available device updates')
    def query(self, args):
        # TODO: Determine notification scheme
        devices = self.session.query(Device).order_by(Device.id)
        if devices:
            for device in devices:
                logger.info('Checking for updates for %s %s', device.vendor_id, device.model)
                if device.has_update():
                    print(device.vendor_id, device.model)
        else:
            logger.info('No devices configured')


    @RegisterCommand('list-vendor', 'Print list of supported vendors')
    def vendor_list(self, args):
        vendors = [{'ID': vendor.__class__.id(), 'Name': vendor.name()} for vendor in registry.values()]
        print(tabulate(vendors, headers='keys'))

    @RegisterCommand('list-devices', 'Provide list of recorded device information')
    def device_list(self, args):
        devices = self.session.query(Device).order_by(Device.id)
        if devices:
            device_list = [device.as_dict() for device in devices]
            print(tabulate(device_list, headers='keys'))
        else:
            logger.info('No devices configured')

    @RegisterCommand('add-device', 'Add a device to be checked', [
        {'name': '--vendor-id', 'choices': registry.keys(), 'help': 'Vendor ID', 'required': True},
        {'name': '--model', 'type': non_empty_argument, 'help': 'Model ID', 'required': True},
        {'name': '--version', 'help': 'Device version'},
        {'name': '--address', 'help': 'IP or web address for the device'},
        {'name': '--description', 'help': 'Description'}])
    def device_add(self, args):
        keys = [c.name for c in Device.__table__.columns if c.name != 'id']
        values = vars(args)
        device = Device(**{k: values[k] for k in keys if k in values})
        self.session.add(device)
        self.session.commit()
        logger.info('Device added with id %d', device.id)

    @RegisterCommand('update-device', 'Update information for an existing device', [
        {'name': '--id', 'help': 'Device ID', 'type': int, 'required': True},
        {'name': '--vendor-id', 'choices': registry.keys(), 'help': 'Vendor ID'},
        {'name': '--model', 'type': non_empty_argument, 'help': 'Model ID'},
        {'name': '--version', 'help': 'Device version'},
        {'name': '--address', 'help': 'IP or web address for the device'},
        {'name': '--description', 'help': 'Description'}])
    def device_update(self, args):
        keys = [c.name for c in Device.__mapper__.columns if c.name != 'id']
        values = vars(args)
        device = self.session.query(Device).get(args.id)
        if not device:
            raise ValueError('Device with id {} not found'.format(args.id))
        for k in keys:
            if k in values:
                device[k] = values[k]
        if self.session.dirty:
            self.session.commit()
            logger.info('Device %d updated', device.id)
        else:
            logger.info('No update to be performed for device %d', device.id)

    @RegisterCommand('delete-device', 'Update information for an existing device', [
        {'name': '--id', 'help': 'Device ID', 'type': int, 'required': True}])
    def device_update(self, args):
        keys = [c.name for c in Device.__mapper__.columns if c.name != 'id']
        values = vars(args)
        device = self.session.query(Device).get(args.id)
        if not device:
            raise ValueError('Device with id {} not found'.format(args.id))
        self.session.delete(device)
        self.session.commit()
        logger.info('Device %d deleted', device.id)


def homenet():
    parser.add_argument('--config', '-c', type=argparse.FileType('r'),
        help='Path to configuration file')
    args = parser.parse_args()
    config = Config(args.config)
    registry.init_config(config)
    log_config = {'level': config.log_level}
    if config.log_file:
        log_config['filename'] = config.log_file,
        log_config['filemode'] = 'a'
    logging.basicConfig(**log_config)
    checker = HomeNetChecker(config)
    args.func(checker, args)

if __name__ == '__main__':
    homenet()
