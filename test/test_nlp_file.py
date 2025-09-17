from app.nlp_api import NLPAPIClient

nlp_client = NLPAPIClient('http://127.0.0.1:8000/api')
srt_url = 'https://lapped-files.oss-cn-beijing.aliyuncs.com/nlp_results/1758116731_4ab15692-bb60-420a-bfc1-8c57a139dfd1.srt?x-oss-signature-version=OSS4-HMAC-SHA256&x-oss-date=20250917T134532Z&x-oss-expires=900&x-oss-credential=LTAI5tF4QU3nvf7zcfzydEmc%2F20250917%2Fcn-beijing%2Foss%2Faliyun_v4_request&x-oss-signature=bea0d7ea4683731fb66e6a29859560de19ad99c18317a173376fc472b9112acd'
local_path = r'D:\dcode\lin_trans\result\f85924006a8670b6d4828fd64c03cc60\tt.srt'
b = nlp_client.download_srt_file(srt_url,local_path)