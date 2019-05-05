#!/usr/bin/python
# coding: utf-8

import os
import sys
import getopt
import boto3
import logging
from templates.lambdas.LambdaTemplate import LambdaTemplate


class Runner(object):

    def __init__(self, stack_name, key_name, change_set_name,
                 token, description, operation,
                 bucket_name, filename):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.stack_name = stack_name
        self.key_name = key_name
        self.change_set_name = change_set_name
        self.token = token
        self.description = description
        self.operation = operation
        self.bucket_name = bucket_name
        self.filename = filename

        self.logger.info("stack_name: %s" % (self.stack_name))
        self.logger.info("key_name: %s" % (self.key_name))
        self.logger.info("change_set_name: %s" % (self.change_set_name))
        self.logger.info("token: %s" % (self.token))
        self.logger.info("description: %s" % (self.description))
        self.logger.info("operation: %s" % (self.operation))
        self.logger.info("bucket_name: %s" % (self.bucket_name))
        self.logger.info("filename: %s" % (self.filename))

    def _upload_file(self):
        """Uploads file to S3

        It is the same as running this command from console:
        aws s3 cp --storage-class STANDARD --no-guess-mime-type --content-type application/x-java-archive
                  target/aws-example-lambda-1.0-SNAPSHOT-jar-with-dependencies.jar s3://guslambda
                --grants full=id=CANONICAL_ID
        """
        key = os.path.basename(self.filename)
        self.logger.info("key: %s" % (key))

        with open(self.filename, 'rb') as data:
            s3_client = boto3.client('s3')
            s3_client.upload_fileobj(
                Fileobj=data,
                Bucket=self.bucket_name,
                Key=key
            )

    def _create_change_set(self):
        """Creates change set

        It is the same as running this command from console:
        aws cloudformation create-change-set --stack-name TropoLambdaGus --template-body file://template.json --no-use-previous-template   \
                                             --parameters file://parameters.json --capabilities CAPABILITY_NAMED_IAM   \
                                             --change-set-name TropoLambdaGus-changeset-1 --client-token Tropolambda-changeset-1   \
                                             --description 'First change set' --change-set-type CREATE
        """
        lambda_template = LambdaTemplate('LambdaTemplate: tropo + boto3')

        cloudformation_client = boto3.client('cloudformation')
        return cloudformation_client.create_change_set(
            StackName=self.stack_name,
            TemplateBody=lambda_template.do_template().to_json(),
            UsePreviousTemplate=False,
            Parameters=[
                {
                    'ParameterKey': 'KeyName',
                    'ParameterValue': self.key_name,
                    'UsePreviousValue': False
                }
            ],
            Capabilities=[
                'CAPABILITY_NAMED_IAM',
            ],
            ChangeSetName=self.change_set_name,
            ClientToken=self.token,
            Description=self.description,
            ChangeSetType=self.operation
        )

    def run(self):
        self._upload_file()

        print(self._create_change_set())


def usage():
    usage_string = """
    SYNOPSIS
        runner.py -s stack_name -f file_name -b bucket_name -k key_name
                  -c change_set_name -t token -d description -o operation

        Where:
            stack_name - Stack name
            file_name - Absolute path to file
            bucket_name - Existing S3 bucket name
            key_name - AWS::EC2::KeyPair::KeyName
            change_set_name - The change set name
            token - Token
            description - The change set description
            operation - Create or update change set. Values: CREATE|UPDATE.
                        CREATE by default.

    """
    print(usage_string)
    sys.exit(1)


def main():
    # Logging information
    logging.basicConfig(filename='output.log', level=logging.DEBUG)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 's:k:c:t:d:o:b:f:')
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(1)

    stack_name = ''
    key_name = ''
    change_set_name = ''
    token = ''
    description = ''
    operation = 'CREATE'
    bucket_name = ''
    filename = ''
    for o, a in opts:
        if o in ('-s', '--stack-name'):
            stack_name = a
        elif o in ('-k', '--key-name'):
            key_name = a
        elif o in ('-c', '--change-set-name'):
            change_set_name = a
        elif o in ('-t', '--token'):
            token = a
        elif o in ('-d', '--description'):
            description = a
        elif o in ('-o', '--operation'):
            operation = a
        elif o in ('-b', '--bucketname'):
            bucket_name = a
        elif o in ('-f', '--filename'):
            filename = a
        elif o in ('-h', '--help'):
            usage()
        else:
            assert False, "unhandled option %s" % (o)

    # Options are required
    if (
        not stack_name or not key_name or not change_set_name or not token or
        not description or not filename or not bucket_name
    ):
        usage()

    Runner(stack_name, key_name, change_set_name,
           token, description, operation,
           bucket_name, filename).run()


if __name__ == '__main__':
    main()
