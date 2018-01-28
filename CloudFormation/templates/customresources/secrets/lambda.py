import logging
from cfnresponse import send, SUCCESS


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    logger.info('got event{}'.format(event))

    if event['RequestType'] == 'Delete':
        send(event, context, SUCCESS)
        return

    response = {
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'RequestId': event['RequestId'],
        'Status': 'SUCCESS',
        'Data': {
            'OutputName1': 'Value1',
            'OutputName2': 'Value2',
         }

    }
    send(response, context, SUCCESS)
    return response
