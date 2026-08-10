from anthropic import Anthropic
from decouple import config

client = Anthropic(
    api_key=config("ANTHROPIC_API_KEY"),  # This is the default and can be omitted
)

message = client.messages.create(
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Hello, Claude",
        }
    ],

    model=config("ANTHROPIC_MODEL"),
)

print(message.content)






#this try for aws benstork

# import boto3
# import json
# # Create Bedrock Runtime client
# client = boto3.client("bedrock-runtime",region_name="us-east-1")
# response = client.invoke_model(
#     modelId="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
#     body=json.dumps({
#         "anthropic_version": "bedrock-2023-05-31",
#         "max_tokens": 200,
#         "messages": [
#             {
#                 "role": "user",
#                 "content": [
#                     {
#                         "type": "text",
#                         "text": "Say hello in one sentence."
#                     }
#                 ]
#             }
#         ]
#     })
# )
# result = json.loads(response["body"].read())
# print(result["content"][0]["text"])