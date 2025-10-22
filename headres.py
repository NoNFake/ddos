import ua_generator

def getHeaders(url: str)-> dict:
    ua = ua_generator.generate(
        device = ['desktop', 'mobile'],
        platform = ['windows', 'macos', 'ios', 'linux', 'android'],
        browser = ['chrome', 'edge', 'firefox', 'safari']
    )
    ua.headers.accept_ch('Sec-CH-UA-Platform-Version, Sec-CH-UA-Full-Version-List')


    header ={
        'Host': url.replace('https://', '').replace('https://', '').split('/')[0],
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json;charset=UTF-8',
        'Token': 'null',
        'Origin': url,
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': url,
        'Accept-Encoding': 'gzip, deflate, br',
        'Priority': 'u=1, i',
    }
    header.update(ua.headers.get())
    return header



# header = getHeaders('https://www.example.com')

# print(header)
