# aws-s3-trigger
Simple repo to test the trigger of an lambda function based off a S3 upload.

The basic idea is we wish to invoke a lambda function to process any packages uploaded to a S3 `<bucket>/inbox` location.  
Based on the contents of this package, the lambda function will call the appropriate business logic such as a step function.

## Create Lambda Function Role
We need to create and IAM role that the can be attached to the lambda function when it is deployed. 
Note the rights in this role may need to be expanded for more complex Lambda functions.  
First create a `trust-policy.json` file that defines the required permissions as shown below.
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": ["lambda.amazonaws.com"]},
      "Action": "sts:AssumeRole"
    }
  ]
}
```
Then create the IAM role in the CLI as shown below. Note I couldn't get this to work on Cloud9 even after running aws 
configure. Please let me know if you know why.

```shell
aws iam create-role --role-name lambda-demo --assume-role-policy-document file://trust-policy.json
```

Next attached the `AWSLambdaBasicExecutionRole` and `AmazonS3FullAccess` policies to the new role to allow the Lambda 
function to write to CloudWatch Logs and access the S3 bucket. This is performed with the following CLI commands.

```shell
aws iam attach-role-policy --role-name lambda-demo --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam attach-role-policy --role-name lambda-demo --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

## Create Lambda to read the object 
The following commands will create the simple lambda function.
```shell
zip package.zip lambda_handler.py
aws lambda create-function \
  --function-name demo-s3-trigger \
  --role arn:aws:iam::<your account id>:role/lambda-demo \
  --runtime python3.8 --timeout 10 --memory-size 128 \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://package.zip
```

It may also be useful to update the package through the CLI with the following command.
```shell
aws lambda update-function-code --function-name  demo-s3-trigger --zip-file fileb://package.zip
```

## Create the S3 Bucket
We need to create a S3 bucket `<bucket>` to upload files into, mine is `demo-s3-trigger` but your will need a different name. Note if the Lambda function writes to this bucket, you'll get into a 
very expensive infinite loop. This requires us to have the `inbox` prefix on the uploaded objects. This prefex can be thought of as a folder.
```shell
aws s3api create-bucket --bucket demo-s3-trigger
aws s3api put-object --bucket demo-s3-trigger --key outbox/
```


## Create the S3 Trigger
Copy the Lambda funtion ARN the above command or the Lambda console into the [s3-trigger.json](s3-trigger.json) as discussed below.

Then we add a resource policy to give s3 permission to invoke the lambda function. You will have to use a different S3 
ARN and account ID. See the [docs](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/lambda/add-permission.html) 
for a full set of options.

```shell
aws lambda add-permission \
  --function-name demo-s3-trigger \
  --statement-id demo-s3-trigger \
  --action "lambda:InvokeFunction" \
  --principal s3.amazonaws.com \
  --source-arn "arn:aws:s3:::<bucket>" \
  --source-account <your account id>
```

To add the trigger we add an event configuration to the S3 bucket, which triggers the Lambda function added above.  
First we create the `s3-trigger.json` config file as shown below (replace the ARN).
```json
{
  "LambdaFunctionConfigurations": [
    {
      "LambdaFunctionArn": <lambda ARN>,
      "Events": ["s3:ObjectCreated:*"]
      "Filter": {
          "Key": {
              "FilterRules": [{"Name": "prefix", "Value": "inbox"}]
          }
      }
    }
  ]
}
```
This configuration is then added to the S3 bucket with the following command. Note that you will have to change your 
bucket name.

```shell
aws s3api put-bucket-notification-configuration --bucket <bucket> \ 
  --notification-configuration file://s3-trigger.json
```

## Test the S3 upload and Lambda trigger
```shell
echo "foo" > bar.txt
aws s3 cp bar.txt s3://demo-s3-trigger/inbox/bar.txt
```


## References
- [C++ Lambda Function with Python Handler](https://github.com/daniel-fudge/aws-lambda-cpp-python#make-iam-role-for-the-lambda-function)
- [Cloud9 C++ Lambda Repo](https://github.com/daniel-fudge/aws-lambda-cpp-cloud9)
- [AWS CLI - Installation](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-linux.html)
- [AWS CLI - Add permissions](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/lambda/add-permission.html)
- [AWS CLI - Invoke Lambda](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html#examples)
- [AWS CLI - Payload Error](https://stackoverflow.com/questions/60310607/amazon-aws-cli-not-allowing-valid-json-in-payload-parameter)
- [AWS S3 API](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/s3api/put-bucket-notification-configuration.html)
- [AWS Lambda Runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)
