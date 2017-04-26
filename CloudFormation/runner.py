#!/usr/bin/python
# coding: utf-8

import sys
import getopt
import boto3
from templates.lambdas.LambdaTemplate import LambdaTemplate


usage_string = """
SYNOPSIS
    runner.py -s stack_name -k key_name -c change_set_name -t token
              -d description -o operation

    Where:
        stack_name - Stack name
        key_name - AWS::EC2::KeyPair::KeyName
        change_set_name - The change set name
        token - Token
        description - The change set description
        operation - Create or update change set. Values: CREATE|UPDATE.
                    CREATE by default.

"""


def _usage():
    print(usage_string)
    sys.exit(1)


def main():

    try:
        opts, args = getopt.getopt(sys.argv[1:], 's:k:c:t:d:o:')
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(1)

    stack_name = ''
    key_name = ''
    change_set_name = ''
    token = ''
    description = ''
    operation = 'CREATE'
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
        elif o in ('-h', '--help'):
            _usage()
        else:
            assert False, "unhandled option %s" % (o)

    # Options are required
    if (
        not stack_name or not key_name or
        not change_set_name or not token or
        not description
    ):
        _usage()

    lambda_template = LambdaTemplate('LambdaTemplate: tropo + boto3')
    client = boto3.client('cloudformation')


    # console command:
    # aws cloudformation create-change-set --stack-name TropoLambdaGus --template-body file://template.json --no-use-previous-template   \
    #                                      --parameters file://parameters.json --capabilities CAPABILITY_NAMED_IAM   \
    #                                      --change-set-name TropoLambdaGus-changeset-1 --client-token Tropolambda-changeset-1   \
    #                                      --description 'First change set' --change-set-type CREATE
    #
    response = client.create_change_set(
        StackName=stack_name,
        TemplateBody=lambda_template.do_template().to_json(),
        UsePreviousTemplate=False,
        Parameters=[
            {
                'ParameterKey': 'KeyName',
                'ParameterValue': key_name,
                'UsePreviousValue': False
            }
        ],
        Capabilities=[
            'CAPABILITY_NAMED_IAM',
        ],
        ChangeSetName=change_set_name,
        ClientToken=token,
        Description=description,
        ChangeSetType=operation
    )

    print(response)

if __name__ == '__main__':

    main()
