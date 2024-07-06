import random
import time
from eth_account.messages import encode_defunct
import requests
from fake_useragent import UserAgent
from config import CACHED_USER_AGENTS, referal_code, THREADS
import json
import threading
from web3.auto import w3
from web3 import Web3
from datetime import datetime

threads = []

polygon = 'https://rpc.ankr.com/polygon'
web3 = Web3(Web3.HTTPProvider(polygon))

def cachedUserAgent(address: str):
    user_agent = CACHED_USER_AGENTS.get(address)
    if user_agent is not None:
        ...
    else:
        user_agent = UserAgent(os="windows").random
        CACHED_USER_AGENTS[address] = user_agent
        with open("data/cached_user_agents.json", "w") as f:
            f.write(json.dumps(CACHED_USER_AGENTS, indent=4))

    return user_agent

def read_file(name: str):
    with open(name, 'r') as file:
        lines = [line.rstrip() for line in file.readlines()]

    return lines



def start_session(address: str):
    session = requests.Session()
    session.headers.update({
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'Origin': 'https://cyber.deform.cc',
        'Content-Type': 'application/json',
        'User-Agent': cachedUserAgent(address),
    })
    return session

def stop_session(session):
    session.close()

def accept_proxy(proxy, session):
    proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
    session.proxies = proxies


def create_message(address, nonce, expires_at):
    message = 'cyber.deform.cc wants you to sign in with your Ethereum account:\n' \
              f'{address}\n\n' \
              'By signing, you are proving you own this wallet and logging in. This does not initiate a transaction or cost any fees.\n\n' \
              'URI: https://cyber.deform.cc\n' \
              'Version: 1\n' \
              'Chain ID: 137\n' \
              f'Nonce: {nonce}\n' \
              f'Issued At: {expires_at}\n' \
              'Resources:\n' \
              '- https://privy.io'
    return message

def create_signature(text, private_key):
    message = encode_defunct(text=text)
    signed_message = w3.eth.account.sign_message(message, private_key=private_key)
    signature = signed_message['signature'].hex()
    return signature

def get_first_token(session, message, signature):
    url = 'https://auth.privy.io/api/v1/siwe/authenticate'
    data = {
        'chainId': 'eip155:137',
        'connectorType': 'injected',
        'message': f'{message}',
        'signature': f'{signature}',
        'walletClientType': 'metamask'
    }
    headers = {
        'Privy-App-Id': 'clphlvsh3034xjw0fvs59mrdc',
        'Origin': 'https://cyber.deform.cc'
    }
    r = session.post(url, json=data, headers=headers).json()
    token = r['token']
    accepted_terms = r['user']['has_accepted_terms']
    return token, accepted_terms

def login(session, first_token):
    url = 'https://api.deform.cc/'
    data = {
        'operationName': 'UserLogin',
        'query': 'mutation UserLogin($data: UserLoginInput!) {\n  userLogin(data: $data)\n}',
        'variables': {
            'data' : {
                'externalAuthToken': f'{first_token}'
            }
        }
    }
    headers = {
        'X-Apollo-Operation-Name': 'UserLogin',
    }
    r = session.post(url, json=data, headers=headers).json()
    token = r['data']['userLogin']

    return token


def compaign_activities(session):
    url = 'https://api.deform.cc/'
    data = {
        'operationName': 'CampaignActivities',
        'query': 'fragment ActivitiesFields on Campaign {\n  activities {\n    id\n    createdAt\n    updatedAt\n    startDateTimeAt\n    endDateTimeAt\n    title\n    description\n    coverAssetUrl\n    type\n    identityType\n    recurringPeriod {\n      count\n      type\n      __typename\n    }\n    recurringMaxCount\n    properties\n    records {\n      id\n      status\n      createdAt\n      __typename\n    }\n    reward {\n      id\n      quantity\n      type\n      __typename\n    }\n    nft {\n      id\n      tokenId\n      name\n      description\n      image\n      properties\n      mintPrice\n      platformFee\n      maxSupply\n      maxMintCountPerAddress\n      nftContract {\n        id\n        address\n        type\n        chainId\n        __typename\n      }\n      __typename\n    }\n    isHidden\n    __typename\n  }\n  __typename\n}\n\nquery CampaignActivities($campaignId: String!) {\n  campaign(id: $campaignId) {\n    id\n    ...ActivitiesFields\n    __typename\n  }\n}',
        'variables': {
            'campaignId': '0c5229f6-de83-43e2-a64c-7d4306b82084'
        }
    }
    headers = {
        'X-Apollo-Operation-Name': 'CampaignActivities',
    }
    r = session.post(url, json=data, headers=headers).json()

    data = {
        'operationName': 'VerifyActivity',
        'query': 'mutation VerifyActivity($data: VerifyActivityInput!) {\n  verifyActivity(data: $data) {\n    record {\n      id\n      status\n      createdAt\n      __typename\n    }\n    __typename\n  }\n}',
        'variables': {
            'data': {
                'activityId': '43692233-3053-4d3c-ba15-b8bec55b5982',
                'metadata': {
                    'referralCode': f'{referal_code}'
                }
            }
        }
    }
    headers = {
        'X-Apollo-Operation-Name': 'VerifyActivity'
    }
    r = session.post(url, json=data, headers=headers).json()
    status = r['data']['verifyActivity']['record']['status']
    print(f'VerifyActivityOutput: {status}')

    data = {
        'operationName': 'UserMe',
        'query': 'query UserMe($campaignId: String!) {\n  userMe {\n    id\n    campaignSpot(campaignId: $campaignId) {\n      id\n      points\n      position\n      referralCount\n      referralCode\n      referralCodeEditsRemaining\n      records {\n        id\n        status\n        points\n        instanceCount\n        createdAt\n        updatedAt\n        activityId\n        activity {\n          id\n          title\n          description\n          type\n          __typename\n        }\n        mission {\n          id\n          title\n          description\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}',
        'variables': {
            'campaignId': '0c5229f6-de83-43e2-a64c-7d4306b82084'
            }
        }
    headers = {
        'X-Apollo-Operation-Name': 'UserMe'
    }
    r = session.post(url, json=data, headers=headers).json()

def visit_cyber_staking_website(session):
    url = 'https://api.deform.cc/'
    data = {
        'operationName': 'VerifyActivity',
        'query': 'mutation VerifyActivity($data: VerifyActivityInput!) {\n  verifyActivity(data: $data) {\n    record {\n      id\n      status\n      createdAt\n      __typename\n    }\n    __typename\n  }\n}',
        'variables': {
            'data': {
                'activityId': 'b4b5de0c-86b1-4a9f-8a24-d3aa3c5a877b'
            }
            }
        }
    headers = {
        'X-Apollo-Operation-Name': 'VerifyActivity'
    }
    r = session.post(url, json=data, headers=headers).json()
    status = r['data']['verifyActivity']['record']['status']
    print(f'Verify visit cyber staking website: {status}')

def learn_more_about_cyber_mainnet_staking(session):
    url = 'https://api.deform.cc/'
    data = {
        'operationName': 'VerifyActivity',
        'query': 'mutation VerifyActivity($data: VerifyActivityInput!) {\n  verifyActivity(data: $data) {\n    record {\n      id\n      status\n      createdAt\n      __typename\n    }\n    __typename\n  }\n}',
        'variables': {
            'data': {
                'activityId': 'ebd19228-c887-4b94-852c-ec1651de2a92'
            }
        }
    }
    headers = {
        'X-Apollo-Operation-Name': 'VerifyActivity'
    }
    r = session.post(url, json=data, headers=headers).json()
    status = r['data']['verifyActivity']['record']['status']
    print(f'Verify learn more about cyber mainnet staking: {status}')

def check_in(session):
    url = 'https://api.deform.cc/'
    data = {
        'operationName': 'VerifyActivity',
        'query': 'mutation VerifyActivity($data: VerifyActivityInput!) {\n  verifyActivity(data: $data) {\n    record {\n      id\n      status\n      createdAt\n      __typename\n    }\n    __typename\n  }\n}',
        'variables': {
            'data': {
                'activityId': '8e3032dd-ad3f-45d3-88e9-cf64050c4a38'
            }
        }
    }
    headers = {
        'X-Apollo-Operation-Name': 'VerifyActivity'
    }
    r = session.post(url, json=data, headers=headers).json()
    if 'errors' in r:
        error = r['errors'][0]['extensions']['clientFacingMessage']
        print(f'Check in еще не доступен: {error}')
    else:
        status = r['data']['verifyActivity']['record']['status']
        print(f'Verify check in: {status}')


def accepted_terms(session, first_token):
    url = 'https://auth.privy.io/api/v1/users/me/accept_terms'
    headers = {
        'Privy-App-Id': 'clphlvsh3034xjw0fvs59mrdc',
        'Authorization': f'Bearer {first_token}'
    }
    r = session.post(url, headers=headers).json()
    accepted_terms = r['has_accepted_terms']
    print(f'Принял соглашение: {accepted_terms}')

def all_requests(private_key, address, session):
    nonce, expires_at = get_info_message(address, session)
    message = create_message(address, nonce, expires_at)
    signature = create_signature(message, private_key)
    first_token, acceptedterms = get_first_token(session, message, signature)
    new_reg = False
    if not acceptedterms:
        new_reg = True
        accepted_terms(session, first_token)

    token = login(session, first_token)
    session.headers.update({
        'Authorization': f'Bearer {token}'
    })
    if new_reg:
        compaign_activities(session)
        visit_cyber_staking_website(session)
        learn_more_about_cyber_mainnet_staking(session)
    check_in(session)

def get_info_message(address, session):
    url = 'https://auth.privy.io/api/v1/siwe/init'
    data = {
        'address': f'{address}'
    }
    headers = {
        'Privy-App-Id': 'clphlvsh3034xjw0fvs59mrdc',
        'Origin': 'https://cyber.deform.cc'
    }
    r = session.post(url, json=data, headers=headers).json()
    nonce = r['nonce']
    expires_at = r['expires_at']
    return nonce, expires_at
def work_thread(private_key,  proxies, semaphore):
    with semaphore:
        while True:
            try:
                wallet = Web3().eth.account.from_key(private_key)
                address = wallet.address
                session = start_session(address)
                accept_proxy(proxies, session)
                all_requests(private_key, address, session)
                stop_session(session)
                break
            except Exception as err:
                print(f'ERROR:{err} : private: {private_key}')


def work():
    semaphore = threading.Semaphore(THREADS)
    private_key = read_file('data/private_key.txt')
    proxy = read_file('data/proxy.txt')
    count = len(private_key)
    i = 0
    while i < count:
        thread = threading.Thread(target=work_thread,
                                  args=(private_key[i], proxy[i], semaphore))
        threads.append(thread)
        thread.start()
        time.sleep(random.randint(1, 2))
        i += 1

def time_work_prog(start_time):
    end_time = time.time()
    execution_time = end_time - start_time
    minutes = int(execution_time // 60)
    seconds = int(execution_time % 60)
    print(f"Время выполнения программы: {minutes} минут {seconds} секунд")

def stop_work():
    file = open('stop_work.txt', 'w')
    file.write(f'{datetime.now()}')
    file.close()

def start_work():
    with open("stop_work.txt", "r") as f:
        last_work = f.read().strip()
    if not last_work:
        return True
    last_work = datetime.strptime(last_work, "%Y-%m-%d %H:%M:%S.%f")
    now = datetime.now()
    flag = (now - last_work).total_seconds() >= 86400
    return flag


if __name__ == "__main__":
    if start_work():
        start_time = time.time()
        work()
        for t in threads:
            t.join()
        time_work_prog(start_time)
        stop_work()
    else:
        print('С последнего ворка не прошло 24 часа.')