require 'aws-sdk-s3'
require 'json'
require 'jwt'

def handler(event:, context:)
    puts event
    
    # return cors headers for preflight check
    if event['routekey'] == "OPTIONS /{proxy+}"
        puts ({step: 'preflight', message: 'preflight CORS check'}.to_json)
        {
            headers: {
                "Access-Control-Allow-Headers": "*, Authorization",
                "Access-Control-Allow-Origin": "https://3000-aynfrancesc-awsbootcamp-5wp8u72n3eu.ws-us94.gitpod.io",
                "Access-Control-Allow-Methods": "OPTIONS,GET,POST"
            },
            statusCode: 200
        }
    else
        token = event['headers']['authorization'].split(' ')[1]
        puts ({step: 'presignedurl', access_token: token}.to_json)


        body_hash = JSON.parse(event["body"])
        extension = body_hash["extension"]
    
        decoded_token = JWT.decode token, nil, false
        puts "decoded token"
        cognito_user_uuid = decoded_token[0]['sub']
       
       
        s3 = Aws::S3::Resource.new
        bucket_name = ENV['UPLOADS_BUCKET_NAME']
        object_key = "#{cognito_user_uuid}.#{extension}"
    
        obj = s3.bucket(bucket_name).object(object_key)
        url = obj.presigned_url(:put, expires_in: 3600)
        url # DATA THAT WILL BE RETURNED
        body = {url: url}.to_json
        {
            headers: {
                "Access-Control-Allow-Headers": "*, Authorization",
                "Access-Control-Allow-Origin": "https://3000-aynfrancesc-awsbootcamp-5wp8u72n3eu.ws-us94.gitpod.io",
                "Access-Control-Allow-Methods": " OPTIONS,GET,POST"
            },
            statusCode: 200,
            body: body
        }
    end
end

