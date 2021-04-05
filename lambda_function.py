def lambda_handler(event, context):
    print("Event:")
    print(event)
    
    file_name = event['Records'][0]['s3']['object']['key'].rsplit('/')[-1]
    
    message = 'Hello there, the package name is {}!'.format(file_name)
    print(message)
    return {'message': message}
