#!/usr/bin/python
# coding: utf-8
#
# Required IAM Role for sending data from Segment to AWS Lambda
#

from troposphere import Parameter, Template, Output, Export, Join, StackName, GetAtt
import troposphere.iam as iam
import awacs.aws as aws
import awacs.awslambda as awslambda
import awacs.sts as sts


class IAMRoleAssumeRoleForLambda(object):

    def __init__(self, sceptre_user_data):
        self.__iam_role_resource_name = 'IAMRoleAssumeRoleForLambda'
        self._template = Template(Description='IAM Role Assume Role For Lambda')
        self._template.AWSTemplateFormatVersion = '2010-09-09'
        self.sceptre_user_data = sceptre_user_data
        self.__add_arguments()
        self.__add_role()
        self.__add_outputs()

    def __add_arguments(self):
        self.project = self._template.add_parameter(Parameter(
            "Project",
            Type="String",
            Description="Project Name",
            MinLength="1",
            MaxLength="255",
            Default='IAM Role Assume Role For Lambda',
            AllowedPattern="[\\x20-\\x7E]*",
            ConstraintDescription="can contain only ASCII characters.",
        ))

    def __add_role(self):
        policy_document_invoke_lambda = aws.Policy(
            Version="2012-10-17",
            Statement=[
                aws.Statement(
                    Effect=aws.Allow,
                    Action=[awslambda.InvokeFunction],
                    Resource=["arn:aws:lambda:eu-west-1:XXXXXXXXX:function:segment-to-kafka-dev-segment"]
                )
            ]
        )
        policy_document_assume_role = aws.Policy(
            Version="2012-10-17",
            Statement=[
                aws.Statement(
                    Effect=aws.Allow,
                    Action=[sts.AssumeRole],
                    Principal=aws.Principal("Service", "lambda.amazonaws.com")
                ),
                aws.Statement(
                    Effect=aws.Allow,
                    Action=[sts.AssumeRole],
                    Principal=aws.AWSPrincipal("arn:aws:iam::595280932656:root"),
                    Condition=aws.Condition(
                        aws.StringEquals({
                            'sts:ExternalId': ['some_external_id']
                        })
                    )
                )
            ]
        )

        role = iam.Role(self.__iam_role_resource_name)
        role.RoleName = "serverless-segment-to-kafka-lambda"
        role.Path = "/"
        role.Policies = [iam.Policy(
            PolicyName="serverless-segment-to-kafka-lambda",
            PolicyDocument=policy_document_invoke_lambda)
        ]
        role.AssumeRolePolicyDocument = policy_document_assume_role
        self._template.add_resource(role)


    def __add_outputs(self):
        self._template.add_output(
            Output(
                "RoleArn",
                Value=GetAtt(self.__iam_role_resource_name, "Arn"),
                Export=Export(Join("-", [StackName, "role-arn"]))

            )
        )
        self._template.add_output(
            Output(
                "RoleId",
                Value=GetAtt(self.__iam_role_resource_name, "RoleId"),
                Export=Export(Join("-", [StackName, "role-id"]))

            )
        )

def sceptre_handler(sceptre_user_data):
    assume_role_for_lambda = IAMRoleAssumeRoleForLambda(sceptre_user_data)
    return assume_role_for_lambda._template.to_json()


if __name__ == '__main__':
    print(sceptre_handler(""))
