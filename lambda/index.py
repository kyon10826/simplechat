# lambda/index.py
import json
import os
import urllib.request
import urllib.parse
from botocore.exceptions import ClientError

# FastAPI endpoint URL - replace with your Google Colab URL
FASTAPI_URL = os.environ.get("FASTAPI_URL", "https://your-colab-url-here")

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))
        
        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")
        
        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])
        
        print("Processing message:", message)
        
        # FastAPIに送信するデータを準備
        data = {
            "message": message,
            "conversation_history": conversation_history
        }
        
        # リクエストの準備
        headers = {
            'Content-Type': 'application/json'
        }
        req = urllib.request.Request(
            FASTAPI_URL,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        # FastAPIエンドポイントを呼び出し
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            print("FastAPI response:", json.dumps(response_data))
            
            if not response_data.get('response'):
                raise Exception("No response content from the API")
            
            assistant_response = response_data['response']
            
            # アシスタントの応答を会話履歴に追加
            conversation_history.append({
                "role": "user",
                "content": message
            })
            conversation_history.append({
                "role": "assistant",
                "content": assistant_response
            })
            
            # 成功レスポンスの返却
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                    "Access-Control-Allow-Methods": "OPTIONS,POST"
                },
                "body": json.dumps({
                    "success": True,
                    "response": assistant_response,
                    "conversationHistory": conversation_history
                })
            }
            
    except Exception as error:
        print("Error:", str(error))
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
