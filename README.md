# CustomEmailSenderWithLambdaTrigger

For this Demo, I used [SAM (Serverless Application Model)](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) to deploy all the required resources with their settings.

# Setup
I deployed a EC2 instance where I will install and provision all the necessary resources. I've also attached an Instance role, so this role can deploy resources.
- We need to SSH or access the EC2 with SSM in order to install all the necessary tools for this DEMO.


1. Installing the required tools on the EC2
```
Update and install packages

$ sudo yum update -y

$ sudo uname -a
Linux ip-172-31-16-164.eu-west-1.compute.internal 6.1.52-71.125.amzn2023.x86_64 #1 SMP PREEMPT_DYNAMIC Tue Sep 12 21:41:38 UTC 2023 x86_64 x86_64 x86_64 GNU/Linux

$ sudo yum install -y git python3-pip tree

$ git -v
# git version 2.40.1

$ python3 --version
Python 3.9.16

$ pip --version
# pip 21.3.1 from /usr/lib/python3.9/site-packages/pip (python 3.9)
```
Then, Installing the AWS CLI
```
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
# You can now run: /usr/local/bin/aws --version

aws --version
# aws-cli/2.13.22 Python/3.11.5 Linux/6.1.52-71.125.amzn2023.x86_64 exe/x86_64.amzn.2023 prompt/off

aws sts get-caller-identity
# {
#     "UserId": "AROATUJEXNAPLE5:i-0fffffffffffffffff",
#     "Account": "012345678912",
#     "Arn": "arn:aws:sts::012345678912:assumed-role/ec2-admin/i-0fffffffffffffffff"
# }
```
Finally, Installing SAM
```
curl -L -o aws-sam-cli-linux-x86_64.zip https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip
unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
sudo ./sam-installation/install
# You can now run: /usr/local/bin/sam --version

sam --version
# SAM CLI, version 1.97.0
```



2. Create a SAM project with Python 3.9
   -  This step will create a directory called `custom_email_sender` where all the necessary files that we will update are there.
   -  We can open the Project with VS Code as well to edit the files that needs to be changed.
```
sam init --name custom_email_sender --runtime python3.9
#         SAM CLI now collects telemetry to better understand customer needs.
# 
#         You can OPT OUT and disable telemetry collection by setting the
#         environment variable SAM_CLI_TELEMETRY=0 in your shell.
#         Thanks for your help!
# 
#         Learn More: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-telemetry.html
# 
# Which template source would you like to use?
#         1 - AWS Quick Start Templates
#         2 - Custom Template Location
# Choice: 1
# 
# Choose an AWS Quick Start application template
#         1 - Hello World Example
#         2 - Hello World Example with Powertools for AWS Lambda
#         3 - Infrastructure event management
#         4 - Multi-step workflow
#         5 - Lambda EFS example
#         6 - Serverless Connector Hello World Example
#         7 - Multi-step workflow with Connectors
# Template: 1
# 
# Based on your selections, the only Package type available is Zip.
# We will proceed to selecting the Package type as Zip.
# 
# Based on your selections, the only dependency manager available is pip.
# We will proceed copying the template using pip.
# 
# Would you like to enable X-Ray tracing on the function(s) in your application?  [y/N]: 
# 
# Would you like to enable monitoring using CloudWatch Application Insights?
# For more info, please view https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch-application-insights.html [y/N]: 
#                                                                                                                                                                                                                                            
# Cloning from https://github.com/aws/aws-sam-cli-app-templates (process may take a moment)                                                                                                                                                  
# 
#     -----------------------
#     Generating application:
#     -----------------------
#     Name: custom_email_sender
#     Runtime: python3.9
#     Architectures: x86_64
#     Dependency Manager: pip
#     Application Template: hello-world
#     Output Directory: .
#     Configuration file: custom_email_sender/samconfig.toml
#     
#     Next steps can be found in the README file at custom_email_sender/README.md
#         
# 
# Commands you can use next
# =========================
# [*] Create pipeline: cd custom_email_sender && sam pipeline init --bootstrap
# [*] Validate SAM template: cd custom_email_sender && sam validate
# [*] Test Function in the Cloud: cd custom_email_sender && sam sync --stack-name {stack-name} --watch
```



3. Edit the template.yaml
   - Let's edit the `custom_email_sender/template.yaml` to create a Lambda function, a user pool and so on.
```
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: >
  custom_email_sender

  Sample SAM Template for custom_email_sender

# More info about Globals: https://github.com/awslabs/serverless-application-model/blob/master/docs/globals.rst
Globals:
  Function:
    Timeout: 5
    MemorySize: 1536

Parameters: 
  CallbackUrl:
    Type: String
    Default: https://www.amazon.com/

Resources:
  CustomerMasterKey:
    Type: AWS::KMS::Key
    Properties:
      Description: A symmetric CMK
      KeyPolicy:
        Version: '2012-10-17'
        Id: key-default-1
        Statement:
        - Sid: Enable IAM User Permissions
          Effect: Allow
          Principal:
            AWS: !Sub arn:aws:iam::${AWS::AccountId}:root
          Action: kms:*
          Resource: '*'
        - Sid: Allow use of the key
          Effect: Allow
          Principal:
            AWS: 
              - !GetAtt CustomEmailSenderTriggerRole.Arn
          Action:
          - kms:DescribeKey
          - kms:Encrypt
          - kms:Decrypt
          - kms:ReEncrypt*
          - kms:GenerateDataKey
          - kms:GenerateDataKeyWithoutPlaintext
          Resource: '*'

  CustomerMasterKeyAlias:
    Type: AWS::KMS::Alias
    Properties: 
      AliasName: !Sub alias/${AWS::StackName}-cognito
      TargetKeyId: !GetAtt CustomerMasterKey.Arn
 
  UserPool:
    Type: "AWS::Cognito::UserPool"
    Properties:
      UserPoolName: !Sub ${AWS::StackName}-UserPool
      AutoVerifiedAttributes:
        - email
      LambdaConfig:
        KMSKeyID: !GetAtt CustomerMasterKey.Arn
        CustomEmailSender: 
          LambdaArn: !GetAtt CustomEmailSenderTrigger.Arn
          LambdaVersion: V1_0

  UserPoolDomain:
    Type: AWS::Cognito::UserPoolDomain
    Properties: 
      Domain: !Sub ${AWS::StackName}-${AWS::AccountId}-${AWS::Region}
      UserPoolId: !Ref UserPool

  UserPoolNoSecretClient:
    Type: "AWS::Cognito::UserPoolClient"
    Description: "App Client without secret"
    Properties:
      UserPoolId: !Ref UserPool
      ClientName: !Sub ${AWS::StackName}-UserPoolClientNoSecret
      GenerateSecret: false
      ExplicitAuthFlows:
        - ALLOW_USER_SRP_AUTH
        - ALLOW_ADMIN_USER_PASSWORD_AUTH
        - ALLOW_USER_PASSWORD_AUTH
        - ALLOW_CUSTOM_AUTH
        - ALLOW_REFRESH_TOKEN_AUTH
      AllowedOAuthFlowsUserPoolClient: true
      SupportedIdentityProviders: 
        - COGNITO
      AllowedOAuthFlows: 
        - code
      AllowedOAuthScopes: 
        - openid
      CallbackURLs: 
        - !Ref CallbackUrl

  UserPoolSecretClient:
    Type: "AWS::Cognito::UserPoolClient"
    Description: "App Client with secret"
    Properties:
      ClientName: !Sub ${AWS::StackName}-UserPoolClientSecret
      GenerateSecret: true
      ExplicitAuthFlows:
        - ALLOW_USER_SRP_AUTH
        - ALLOW_ADMIN_USER_PASSWORD_AUTH
        - ALLOW_USER_PASSWORD_AUTH
        - ALLOW_CUSTOM_AUTH
        - ALLOW_REFRESH_TOKEN_AUTH
      UserPoolId: !Ref UserPool

  CustomEmailSenderTrigger:
    Type: AWS::Serverless::Function # More info about Function Resource: https://github.com/awslabs/serverless-application-model/blob/master/versions/2016-10-31.md#awsserverlessfunction
    Properties:
      CodeUri: hello_world/
      Handler: custom_email_sender_trigger.lambda_handler
      Runtime: python3.9
      Environment:
        Variables:
          KEY_ID: !GetAtt CustomerMasterKey.Arn
          KEY_ALIAS: !Sub arn:aws:kms:${AWS::Region}:${AWS::AccountId}:${CustomerMasterKeyAlias}
      Policies:
        - Statement:
          - Sid: SES
            Effect: Allow
            Action:
              - ses:SendEmail
            Resource: '*'

  CustomEmailSenderTriggerPermission:
    Type: AWS::Lambda::Permission
    Properties: 
      Action: lambda:InvokeFunction
      FunctionName: !GetAtt CustomEmailSenderTrigger.Arn
      Principal: cognito-idp.amazonaws.com
      SourceArn: !Sub arn:aws:cognito-idp:${AWS::Region}:${AWS::AccountId}:userpool/${UserPool}

Outputs:
  UserPoolId:
    Value: !Ref UserPool
  UserPoolNoSecretClientId:
    Value: !Ref UserPoolNoSecretClient
  UserPoolSecretClientId:
    Value: !Ref UserPoolSecretClient
  LoginEndpoint: 
    Value: !Sub "https://${UserPoolDomain}.auth.${AWS::Region}.amazoncognito.com/login?redirect_uri=${CallbackUrl}&response_type=CODE&client_id=${UserPoolNoSecretClient}&scope=openid"
  UserPoolVariables:
    Value: !Sub |

      region=${AWS::Region}
      user_pool_id=${UserPool}
      client_id=${UserPoolNoSecretClient}
```


4. Create a Lambda function
 - Create a new python file `hello_world/custom_email_sender_trigger.py` where we'll be using the [following code](https://github.com/Yorlin2S/CustomEmailSenderWithLambdaTrigger/blob/main/lambda.py) to receive and send emails accordingly


5. Being sure to have the following packages declared in `hello_world/requirements.txt
```
requests
boto3
aws_encryption_sdk
```

6. The structure of the directory `custom_email_sender` should look like as follows.
```
$ tree -L 2 -a
# .
# ├── .gitignore
# ├── README.md
# ├── __init__.py
# ├── events
# │   └── event.json
# ├── hello_world
# │   ├── __init__.py
# │   ├── app.py
# │   ├── custom_email_sender_trigger.py
# │   └── requirements.txt
# ├── template.yaml
# └── tests
#     ├── __init__.py
#     ├── integration
#     ├── requirements.txt
#     └── unit
```

7. Build and deploy resources
   - Next, we are going to build and deploy with AWS SAM CLI. If successful, AWS SAM CLI will create a Customer Managed Key, a trigger and a user pool and an app client. Please note the UserPoolVariables in Outputs.

```
$ export region=eu-west-1
$ export stack_name=custom-email-sender-1
$ sam build && sam deploy --region ${region} --stack-name ${stack_name} --resolve-s3 --capabilities CAPABILITY_NAMED_IAM
# ...
# Outputs
# ----
# ...
# Key                 UserPoolNoSecretClientId
# Description         -
# Value               EXAMPLEl2f6rjkqkbji2qr3u
# Key                 UserPoolId
# Description         -
# Value               eu-west-1_EXAMPLE
# Key                 LoginEndpoint
# Description         -
# Value               https://custom-email-sender-1-012345678912-eu-west-1.auth.eu-west-1.amazoncognito.com/login?redirect_uri=https://www.amazon.com/&response_type=CODE&client_id=EXAMPLEl2f6rjkqkbji2qr3u&scope=openid                                                      
# Key                 UserPoolSecretClientId
# Description         -
# Value               EXAMPLEb0p566mb613bdvcg
# Key                 UserPoolVariables
# Description         -
# Value
# region=eu-west-1
# user_pool_id=eu-west-1_EXAMPLE
# client_id=EXAMPLEl2f6rjkqkbji2qr3u
# Successfully created/updated stack - custom-email-sender-1 in eu-west-1
```

9. SignUp to send an email notification.
    - Next, we are going to sign up to send an email notification. Please use the value of the UserPoolVariables in Outputs and replace username / password / email with yours.
    - Tested the lambda Code with Sign up only but it can be any of the events mentioned [here](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-custom-email-sender.html#trigger-source)

```
$ export region=eu-west-1
$ export user_pool_id=eu-west-1_EXAMPLE
$ export client_id=EXAMPLEl2f6rjkqkbji2qr3u

$ export username=HenryFord
$ export password=Pass_@1234
$ export email=${username}@example.com

aws --region ${region} cognito-idp sign-up --client-id ${client_id} --username ${username} --password ${password} --user-attributes Name=email,Value=${email}
{
    "UserConfirmed": false,
    "CodeDeliveryDetails": {
        "Destination": "H***@e***",
        "DeliveryMedium": "EMAIL",
        "AttributeName": "email"
    },
    "UserSub": "37877a9f-a4d4-4ae9-b20c-f59890e04411"
}
```

10. Check exection logs
    - The CustomEmailSenderTrigger should be invoked by SignUp API.

```
$ sam logs --region ${region} --stack-name ${stack_name}
# INIT_START Runtime Version: python:3.9.v31      Runtime Version ARN: arn:aws:lambda:eu-west-1::runtime:70cc0ac5269c3c6665655653f4f51fe0e3fcaa3ec661249a16dbb0d8e6c3a502
# START RequestId: 1ab0f25d-c50e-448d-aa3f-d21b73e93c41 Version: $LATEST
# {
#   "version": "1",
#   "triggerSource": "CustomEmailSender_SignUp",
#   "region": "eu-west-1",
#   "userPoolId": "eu-west-1_EXAMPLE",
#   "userName": "HenryFord",
#   "callerContext": {
#     "awsSdkVersion": "aws-sdk-unknown-unknown",
#     "clientId": "EXAMPLEl2f6rjkqkbji2qr3u"
#   },
#   "request": {
#     "type": "customEmailSenderRequestV1",
#     "code": "AYADeJsc8ABfz4We35yeVQUr6A8AgQACABVhd3MtY3J5cHRvLXB1YmxpYy1rZXkAREF1c29tTFBxVGJHZ3BKaHlJMGJVVFVIcGk3bEl4SmhMNVBMejExc043YmI0MzNLb1RVbWZYTzBMV3JZYzFsS1N6Zz09AAt1c2VycG9vbC1pZAATZXUtd2VzdC0xX1VWY3d2WjFFOAABAAdhd3Mta21zAEthcm46YXdzOmttczpldS13ZXN0LTE6MjQ5NzU5Mzk4OTM0OmtleS84YTIzMTAyYy05YjY4LTRmZWQtODJjZS01MjNjNTM2MzUzOWUAuAECAQB4zjtU8csJUK3MLH8Y6WeSR/UlTZ5dBq+1YWcTwrPeeIUB/sLrtmrF6weu6juPsOHF/gAAAH4wfAYJKoZIhvcNAQcGoG8wbQIBADBoBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDGJqb9919luTGmPbEgIBEIA7wHTDUaKbPmKtg6QETi2TiVJK7tvfTZRP4VWFGxmB5/0lhcAiKTA7EGweo1/BTKTk0x4b3LiluzDd+yMCAAAAAAwAABAAAAAAAAAAAAAAAAAALZddEWiNl+OGHRMKbclmQf////8AAAABAAAAAAAAAAAAAAABAAAABvMlKUZN7tCz953A13RxWz39z56LZ2QAZzBlAjAR+8fFCOlFWEm0hFajxMCD3C3Tuo76l0pJicv6yRw0hQbRHcoD+3RJcvxyX8cq1yMCMQDhZrrFr90sDr1NuKJew6oLDuBFZUz3pIXOe3hJb1/gi1bfN1t/EXAMPLE=",
#     "clientMetadata": null,
#     "userAttributes": {
#       "sub": "37877a9f-a4d4-4ae9-b20c-f59890e04411",
#       "email_verified": "false",
#       "cognito:user_status": "UNCONFIRMED",
#       "email": "HenryFord@example.com"
#     }
#   }
# }
# 982921
# MessageHeader...
```
      
