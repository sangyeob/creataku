"""
ElasticBox Confidential
Copyright (c) 2012 All Right Reserved, ElasticBox Inc.

NOTICE:  All information contained herein is, and remains the property
of ElasticBox. The intellectual and technical concepts contained herein are
proprietary and may be covered by U.S. and Foreign Patents, patents in process,
and are protected by trade secret or copyright law. Dissemination of this
information or reproduction of this material is strictly forbidden unless prior
written permission is obtained from ElasticBox
"""

import json
import pipes
import os
import hashlib
import shutil
import stat
import StringIO
import yaml
import requests
import logging
import urlparse

from requests import codes

ELASTICBOX_RELEASE = '4.0'
ELASTICBOX_CREDENTIALS_NAME = 'ElasticBox Token'
ELASTICBOX_CREDENTIALS_ACCOUNT = 'elasticbox'
ELASTICBOX_TOKEN_HEADER = 'ElasticBox-Token'
ELASTICBOX_RELEASE_HEADER = 'ElasticBox-Release'

TAGS_ARG = ['-t', '--tags'], {'help': 'Tags', 'nargs': '*'}
CLAIMS_ARG = ['-c', '--claims'], {'help': 'Claims', 'nargs': '*'}
REQUIREMENTS_ARG = ['-r', '--requirements'], {'help': 'Requirements', 'nargs': '*'}
RECURSIVE_ARG = ['-r', '--recursive'], {'help': 'Recursive', 'action': 'store_false'}
VARIABLE_ARG = ['-v', '--variable'], {'help': 'Variable', 'nargs': 2}
BOX_ID_ARG = ['-b', '--box-id'], {'help': 'Box ID'}
WORKSPACE_ID_ARG = ['-w', '--workspace-id'], {'help': 'Workspace ID'}
INSTANCE_ID_ARG = ['-i', '--instance-id'], {'help': 'Instance ID'}
FIELDS_ARG = ['-f', '--fields'], {'help': 'Fields of the resource', 'nargs': '*'}
COMMENT_ARG = ['-m', '--comment'], {'help': 'Add comment to version'}
IMAGE_ARG = ['--image'], {'help': 'Docker base image'}
BOXES_PATH_ARG = ['--boxes-path'], {'help': 'Path where boxes are stored', 'dest': 'path', 'default': os.getcwd()}

DEFAULT_WORKSPACE_FIELDS = ['id', 'name']
DEFAULT_BOX_FIELDS = ['id', 'name', 'owner', 'requirements']
DEFAULT_INSTANCE_FIELDS = ['id', 'name', 'owner', 'tags']


# Disable InsecurePlatformWarning
requests.packages.urllib3.disable_warnings()


def add_standard_argument(parser, argument, **kwargs):
    name = argument[0]
    options = argument[1]

    if kwargs:
        options.update(kwargs)

    parser.add_argument(*name, **options)


class TermColors:  # pylint: disable=R0903
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class AuthTokenException(Exception):
    pass


class ApiException(Exception):

    def __init__(self, message, status_code):
        Exception.__init__(self, message)

        self.status_code = status_code


class NotFoundException(ApiException):
    pass


class ForbiddenException(ApiException):
    pass


class UnauthorizedException(ApiException):
    pass


class AuthenticatedSession(object):

    def __init__(self, url, token):
        parsed_url = urlparse.urlparse(url)
        if not parsed_url.scheme:
            self._url = 'https://{0}'.format(parsed_url.geturl())
        else:
            self._url = parsed_url.geturl()

        self._session = requests.Session()
        self._session.headers.update({ELASTICBOX_TOKEN_HEADER: token})
        self._session.headers.update({ELASTICBOX_RELEASE_HEADER: ELASTICBOX_RELEASE})

    def get(self, url_path, *args):
        if url_path.startswith('/'):
            url = self._url + url_path.format(*args)
        else:
            url = self._url + '/' + url_path.format(*args)

        response = self._session.get(url, verify=False)

        if response.status_code != codes['ok']:
            logging.debug(response.text)
            try:
                message = response.json()['message']
            except ValueError:
                message = "GET {0} returned {1}".format(url, response.status_code)

            raise AuthenticatedSession._create_exception(message, response.status_code)
        else:
            return response

    def delete(self, url_path, *args):
        if url_path.startswith('/'):
            url = self._url + url_path.format(*args)
        else:
            url = self._url + '/' + url_path.format(*args)

        response = self._session.delete(url, verify=False)

        if response.status_code not in [codes['ok'], codes['accepted'], codes['no_content']]:
            logging.debug(response.text)
            try:
                message = response.json()['message']
            except ValueError:
                message = "DELETE {0} returned {1}".format(url, response.status_code)

            raise AuthenticatedSession._create_exception(message, response.status_code)
        else:
            return response

    def put(self, url_path, *args, **kwargs):
        if url_path.startswith('/'):
            url = self._url + url_path.format(*args)
        else:
            url = self._url + '/' + url_path.format(*args)

        response = self._session.put(url, verify=False, **kwargs)

        if response.status_code not in [codes['ok'], codes['accepted'], codes['no_content'], codes['created']]:
            logging.debug(response.text)
            try:
                message = response.json()['message']
            except ValueError:
                message = "PUT {0} returned {1}".format(url, response.status_code)

            raise AuthenticatedSession._create_exception(message, response.status_code)
        else:
            return response

    def post(self, url_path, *args, **kwargs):
        if url_path.startswith('/'):
            url = self._url + url_path.format(*args)
        else:
            url = self._url + '/' + url_path.format(*args)

        response = self._session.post(url, verify=False, **kwargs)

        if response.status_code not in [codes['ok'], codes['accepted'], codes['no_content'], codes['created']]:
            logging.debug(response.text)
            try:
                message = response.json()['message']
            except ValueError:
                message = "POST {0} returned {1}".format(url, response.status_code)

            raise AuthenticatedSession._create_exception(message, response.status_code)
        else:
            return response

    @staticmethod
    def _create_exception(message, status_code):
        if status_code == codes['not_found']:
            return NotFoundException(message, status_code)
        elif status_code == codes['unauthorized']:
            return UnauthorizedException(message, status_code)
        elif status_code == codes['forbidden']:
            return ForbiddenException(message, status_code)
        else:
            return ApiException(message, status_code)


class Formatter(object):

    def __init__(self, args):
        self._json = args.json if 'json' in args else False
        self._fields = args.fields if 'fields' in args else False
        self._verbose = args.verbose if 'verbose' in args else False

    def write(self, resources, prefix=None, fields=None):
        if type(resources) is list:
            self._write_collection(resources, fields)
        else:
            self._write_object(resources, prefix, fields)

    def _write_object(self, resource, prefix, fields):
        fields = fields or self._fields

        if self._json:
            print json.dumps(resource, indent=4)

        elif fields:
            for field in fields:
                if '.' in field:
                    level = resource
                    properties = field.split('.')
                    member = properties.pop()

                    for name in properties:
                        if name in level:
                            level = level[name]

                    value = Formatter._format(level.get(member))
                else:
                    value = Formatter._format(resource.get(field))

                if value:
                    name = field.upper().replace('.', '_')
                    value = pipes.quote(value)

                    if prefix:
                        name = '{0}_{1}'.format(prefix.upper(), name)

                    print '{0}={1}'.format(name, value)

    def _write_collection(self, resources, fields):
        fields = self._fields or fields

        if self._json:
            print json.dumps(resources, indent=4)

        elif fields:
            table = [Formatter._flatten(resource, fields) for resource in resources]
            widths = [len(field) for field in fields]

            for row in table:
                for index, column in enumerate(row):
                    widths[index] = max(len(column), widths[index])

            if self._verbose:
                headers = []
                separator = []

                for index, field in enumerate(fields):
                    headers += ['{:{}}'.format(field, widths[index])]
                    separator += ['-' * widths[index]]

                print '\t'.join(headers)
                print '\t'.join(separator)

            for row in table:
                data = []
                for index, column in enumerate(row):
                    if widths[index] > 0:
                        data += ['{:{}}'.format(column, widths[index])]

                print '\t'.join(data)

    @staticmethod
    def _flatten(resource, fields):
        table = []

        for field in fields:
            if '.' in field:
                level = resource
                properties = field.split('.')
                member = properties.pop()

                for name in properties:
                    if name in level:
                        level = level[name]

                value = Formatter._format(level.get(member))
            else:
                value = Formatter._format(resource.get(field))

            table.append(value)

        return table

    @staticmethod
    def _format(value):
        if not value:
            return ''
        elif type(value) is list:
            return ','.join(value)
        elif type(value) is dict:
            return "(%s)" % ','.join(value.keys())
        else:
            return str(value)


class Boxes(object):

    def __init__(self, path, session=None):
        self._session = session
        self._path = path
        self._box_index = {}

        if os.path.exists(self._path):
            for item in os.listdir(self._path):
                box_path = os.path.join(self._path, item, 'box.yaml')
                if os.path.exists(box_path):
                    with open(box_path, 'r') as box_file:
                        box = yaml.load(box_file)
                        self._box_index[box['id']] = box

    def get_path(self):
        return self._path

    def has_box(self, box_ref):
        for box in self._box_index.values():
            if box['name'] == box_ref:
                return True

        return box_ref in self._box_index

    def get_box(self, box_ref):
        if box_ref in self._box_index:
            return self._box_index[box_ref]
        else:
            for box in self._box_index.values():
                if box['name'] == box_ref:
                    return box

        raise Exception("Box '%s' not found." % box_ref)

    def copy_box(self, box_ref, destination):
        box = self.get_box(box_ref)
        destination_folder = os.path.join(destination, box['name'])

        if os.path.exists(destination_folder):
            shutil.rmtree(destination_folder)

        shutil.copytree(os.path.join(self._path, box['name']), destination_folder)

    def export_box(self, box_ref, recursive=False, source=None):
        if source and source.has_box(box_ref):
            self._export_local_box(box_ref, recursive, source)
        else:
            self._export_remote_box(box_ref, recursive, source)

    def export_instance_boxes(self, instance_id):
        instance = self._session.get('/services/instances/{0}', instance_id).json()
        for box in instance['boxes']:
            self._export_box_document(box, False, None)

    def import_box(self, box_ref, comment=None, workspace=None, docker_image=None):
        box = self.get_box(box_ref)
        box['members'] = []

        if 'id' in box:
            current = self._get_remote_box_by_id(box['id'])
            if not current:
                current = self._get_remote_box_by_name(workspace, box['name'])

        if current:
            box['members'] = current['members']
            box['owner'] = current['owner']
            box['organization'] = current['organization']
        else:
            box['members'] = []
            profile = self._session.get('/services/profile').json()
            profile_ws = self._session.get('/services/workspaces/{0}', profile['workspace']).json()
            box['organization'] = profile_ws['organization']

        if workspace:
            box['owner'] = workspace

        self._merge_icon(box, current)
        self._merge_readme(box, current)
        self._merge_variables(box, current)
        self._merge_events(box, current)

        if current:
            if 'version' in current:
                box['version'] = {
                    "box": current['version']['box'],
                    "description": comment or "Version created using ebcli",
                    "number": current['version']['number']
                }
            else:
                box['version'] = {
                    "box": current['id'],
                    "description": comment or "Version created using ebcli",
                    "number": {'major': 0, 'minor': 0, 'patch': 0}
                }

        if current and docker_image:
            box['version']['container_url'] = docker_image

        box['schema'] = "http://elasticbox.net/schemas/boxes/script"
        if current:
            self._session.put('/services/boxes/{0}', box['version']['box'], json=box)
        else:
            print box
            self._session.post('/services/boxes', json=box)

    def _merge_events(self, box, current):
        box['events'] = dict()
        for event in ['pre_install', 'install', 'pre_configure', 'configure', 'pre_start', 'start',
                      'stop', 'post_stop', 'terminate', 'post_terminate']:

            script_path = os.path.join(self._path, box['name'], 'events', event)
            if os.path.exists(script_path):
                if current and event in current['events']:
                    current_script = current['events'].get(event)
                    file_reference = self._upload_file(script_path, current_script['url'])
                else:
                    file_reference = self._upload_file(script_path)

                if file_reference:
                    box['events'][event] = file_reference
                else:
                    box['events'][event] = current_script

    def _merge_variables(self, box, current):
        for variable in box['variables']:
            if variable['type'] == 'File' and variable['value']:
                file_variable_path = os.path.join(self._path, box['name'], variable['value'])
                if current:
                    existing = Boxes._find_variable(current['variables'], variable['name'])
                else:
                    existing = None

                if existing:
                    file_reference = self._upload_file(file_variable_path, existing['value'])
                else:
                    file_reference = self._upload_file(file_variable_path)

                if file_reference:
                    variable['value'] = file_reference['url']
                else:
                    variable['value'] = existing['value']

    def _merge_readme(self, box, current):
        readme_path = os.path.join(self._path, box['name'], 'readme.MD')
        if os.path.exists(readme_path):
            if current and 'readme' in current:
                file_reference = self._upload_file(readme_path, current['readme']['url'])
            else:
                file_reference = self._upload_file(readme_path)

            if file_reference:
                box['readme'] = file_reference
            else:
                box['readme'] = current.get('readme')

    def _merge_icon(self, box, current):
        if 'icon' in box:
            icon_path = os.path.join(self._path, box['name'], box['icon'])
            if current and 'icon' in current:
                file_reference = self._upload_file(icon_path, current['icon'])
            else:
                file_reference = self._upload_file(icon_path)

            if file_reference:
                box['icon'] = file_reference['url']
            elif current:
                box['icon'] = current.get('icon')

    def _get_remote_box_by_id(self, box_id):
        try:
            versions = self._session.get('/services/boxes/{0}/versions', box_id).json()

            if len(versions) == 0:
                box = self._session.get('/services/boxes/{0}', box_id).json()
            else:
                box = versions.pop(0)

            for version in versions:
                if box.get('version') and version.get('version') and \
                        version['version']['number']['major'] >= box['version']['number']['major'] and \
                        version['version']['number']['minor'] >= box['version']['number']['minor'] and \
                        version['version']['number']['patch'] > box['version']['number']['patch']:
                    box = version

        except NotFoundException:
            box = None

        return box

    def _get_remote_box_by_name(self, workspace, name):
        boxes = self._session.get('/services/workspaces/{0}/boxes', workspace).json()

        for box in boxes:
            if box['owner'] == workspace and box['name'] == name:
                return self._get_remote_box_by_id(box['id'])

        return None

    def _export_local_box(self, box_id, recursive, source):
        source.copy_box(box_id, self._path)
        box = source.get_box(box_id)
        self._box_index[box_id] = box

        for variable in box['variables'] if 'variables' in box else []:
            if variable['type'] == 'Box' and recursive:
                self.export_box(variable['value'], recursive, source)

    def _export_remote_box(self, box_id, recursive, source):
        box = self._session.get('/services/boxes/{0}', box_id).json()
        self._export_box_document(box, recursive, source)

    def _export_box_document(self, box, recursive, source):
        box_path = os.path.join(self._path, box['name'])
        box_files_path = os.path.join(box_path, 'files')
        box_events_path = os.path.join(box_path, 'events')

        if not os.path.exists(box_path):
            os.makedirs(box_events_path)
            os.makedirs(box_files_path)

        document = dict()
        document['variables'] = []

        for key in ['id', 'name', 'description', 'requirements']:
            if key in box:
                document[key] = box[key]

        if 'readme' in box:
            self._download_file(os.path.join(box_path, 'readme.MD'), box['readme']['url'])

        if 'icon' in box:
            document['icon'] = os.path.basename(box['icon'])
            self._download_file(os.path.join(box_path, document['icon']), box['icon'])

        for variable in box['variables']:
            if variable['type'] == 'File' and variable['value']:
                filename = os.path.basename(variable['value'])
                self._download_file(os.path.join(box_files_path, filename), variable['value'])
                variable['value'] = os.path.join('files', filename)
            elif variable['type'] == 'Box' and recursive:
                self.export_box(variable['value'], recursive, source)

            document['variables'].append(variable)

        for name, event in box['events'].iteritems():
            self._download_file(os.path.join(box_events_path, name), event['url'])
            os.chmod(os.path.join(box_events_path, name), stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR)

        self._save_box(document)

    def _save_box(self, box):
        box_path = os.path.join(self._path, box['name'], 'box.yaml')

        box_yaml = StringIO.StringIO()
        yaml.safe_dump(
            box,
            stream=box_yaml,
            encoding='utf-8',
            allow_unicode=True,
            default_flow_style=False)

        if os.path.exists(box_path):
            with open(box_path, 'r') as box_file:
                if box_yaml.getvalue() == box_file.read():
                    return

        with open(box_path, 'wb') as box_file:
            print >> box_file, box_yaml.getvalue()

        self._box_index[box['id']] = box

    def _upload_file(self, file_path, existing=None):
        if os.path.exists(file_path):
            with open(file_path, 'rb') as destination:
                contents = destination.read()
        else:
            raise Exception("File not found '{0}'.".format(file_path))

        if existing:
            remote = self._session.get(existing).content
            if hashlib.md5(contents).hexdigest() == hashlib.md5(remote).hexdigest():
                return None

        files = dict()
        files[os.path.basename(file_path)] = contents

        return self._session.post('/services/blobs/upload', files=files).json()

    def _download_file(self, file_path, url_path):
        content = self._session.get(url_path).content
        overwrite = True

        if os.path.exists(file_path):
            with open(file_path, 'r') as destination:
                file_hash = hashlib.md5(destination.read()).hexdigest()

            overwrite = file_hash != hashlib.md5(content).hexdigest()

        if overwrite:
            with open(file_path, 'w') as destination:
                destination.write(content)

    @staticmethod
    def _find_variable(variables, name):
        for variable in variables:
            if variable['name'] == name:
                return variable
