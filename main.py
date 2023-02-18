import httpx, random, string, time, os, ctypes, tls_client
import concurrent.futures
from account_generator_helper import GmailNator
from colorama import Fore

os.system("cls")
accounts_made=0
balance_total=0

ref_code = ""
threads=10
discord_token="" #they dont check this either so u just need 1 token

headers={
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "sv-SE,sv;q=0.9",
    "authorization": "Bearer null",
    "content-type": "application/json",
    "origin": "https://dashboard.capsolver.com",
    "referer": "https://dashboard.capsolver.com/",
    "sec-ch-ua": '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
}

class other():
    def get_proxy():
        proxy = random.choice(open("proxies.txt","r").read().splitlines())
        return  {
                            "http://":f"http://{proxy}",
                            "https://":f"http://{proxy}"
                }

    def do_oauth2():
        url="https://discord.com/api/v9/oauth2/authorize?client_id=1062177869834502194&response_type=code&redirect_uri=https%3A%2F%2Fdashboard.capsolver.com%2Foauth2%2Fdiscord.html&scope=identify%20email%20guilds.join"

        discord = httpx.post(url,headers={
                        "authorization": discord_token,
                        "content-type": "application/json"
                    },json={
                        "permissions": "0",
                        "authorize": True
                    })
        if discord.status_code==200:
            print(f"{Fore.LIGHTBLUE_EX}Successfully linked discord")
            return discord.json()["location"].split("?code=")[1]

class capsolver():
    def send(email,proxy):
        req = httpx.post("https://backend.captchaai.io/api/v1/passport/account/email/send",proxies=proxy, headers=headers, json={
                    "email": email
                }).json()
        if req["success"]: return True
        else: return False

    def discord_oauth2(access_token,proxy):
        headers["authorization"]="Bearer "+access_token
        session = tls_client.Session(
            client_identifier="chrome_108",
            random_tls_extension_order=True
        )#the req gets fucked using httpx

        discord = session.get("https://backend.captchaai.io/api/v1/oauth2/authorize_url/discord",proxies=proxy,headers=headers).json()
        return discord["url"]

    def login(email, password, proxy):
        account = httpx.post("https://backend.captchaai.io/api/v1/passport/login",headers=headers,json={
                    "email": email,
                    "password": password,
                    "recaptchaToken": ''.join(random.sample(string.ascii_letters+string.digits,10))#FIRE CHECKS
                },proxies=proxy).json()
        
        return account["accessToken"]

    def verify_oauth2(code,access_token,proxy):
        headers["authorization"]="Bearer "+access_token
        account = httpx.post("https://backend.captchaai.io/api/v1/oauth2/verify/discord",headers=headers,json={
                    "code": code
                },proxies=proxy).json()
        
        return account["token"], account["balance"]

    def make_account(proxy):
        global accounts_made, balance_total
        mail = GmailNator()
        email = mail.get_email_online(True,True,True)
        mail.set_email(email)
        print(f"{Fore.LIGHTMAGENTA_EX}{email}")
        status=capsolver.send(email,proxy)
        
        if status:
            print(f"{Fore.YELLOW}Sent email")
            while len(mail.get_inbox()) == 0:
                pass
            code=mail.get_inbox()[0].letter.split('<center style="color: #ffffff; font-family: sans-serif; font-size: 15px;">')[1].split("</center>")[0].replace(' ', '').replace('\r', '').replace('\n', '')

            print(f"{Fore.CYAN}Got code --> {code}")
            password=''.join(random.sample(string.ascii_letters+string.digits,10))
            account = httpx.post("https://backend.captchaai.io/api/v1/passport/account/email/reg", headers=headers, json={
                                "email": email,
                                "code": code,
                                "username": email,
                                "password": password,
                                "inviteCode": ref_code,
                                "recaptchaToken": ''.join(random.sample(string.ascii_letters+string.digits,10))#FIRE CHECKS
                            },proxies=proxy).text

            if "New user registered successfully" in account:
                print(f"{Fore.LIGHTGREEN_EX}Account made{Fore.LIGHTWHITE_EX} ({email}:{password})")
                accounts_made+=1
                access_token = capsolver.login(email, password, proxy)

                code = other.do_oauth2()
                api_key, balance = capsolver.verify_oauth2(code,access_token,proxy)
                print(f"{Fore.BLUE}{api_key} --> balance: {Fore.LIGHTWHITE_EX}${str(balance)}")
                balance_total+=float(balance)
                ctypes.windll.kernel32.SetConsoleTitleW(f"capsolver fucker | accounts made: {str(accounts_made)} threads: {str(threads)} balance: ${round(balance_total,3)}")

                with open("accs.txt","a+") as b:
                    b.write(f"{email}:{password}:{api_key}+\n")
            else:
                print(f"{Fore.RED}Failed to make account")

        else:
            print(f"{Fore.RED}Failed to send email")

with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
    while True:
        executor.submit(capsolver.make_account, other.get_proxy())
