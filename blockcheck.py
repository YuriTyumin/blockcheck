#!/usr/bin/env python3
# coding: utf-8
import argparse
import urllib.request
import urllib.parse
import dns.resolver
try:
    import tkinter as tk
    import threading
    import queue
    tkusable = True

    class ThreadSafeConsole(tk.Text):
        def __init__(self, master, **options):
            tk.Text.__init__(self, master, **options)
            self.queue = queue.Queue()
            self.update_me()
        def write(self, line):
            self.queue.put(line)
        def clear(self):
            self.queue.put(None)
        def update_me(self):
            try:
                while 1:
                    line = self.queue.get_nowait()
                    if line is None:
                        self.delete(1.0, tk.END)
                    else:
                        self.insert(tk.END, str(line))
                    self.see(tk.END)
                    self.update_idletasks()
            except queue.Empty:
                pass
            self.after(100, self.update_me)

except ImportError:
    tkusable = False

    class ThreadSafeConsole():
        pass

def print(*args, **kwargs):
    if tkusable:
        for arg in args:
            text.write(str(arg))
        text.write("\n")
    else:
        __builtins__.print(*args, **kwargs)

def _get_a_records(sitelist, dnsserver = None):
    resolver = dns.resolver.Resolver()
    resolver.timeout = 5
    resolver.lifetime = 5
    
    if dnsserver:
        resolver.nameservers = [dnsserver]

    result = []
    for site in sitelist:
        try:
            for item in resolver.query(site).rrset.items:
                result.append(item.to_text())
        except:
            return ""

    return sorted(result)

def _get_url(url, proxy = None, ip = None):
    if ip:
        parsed_url = list(urllib.parse.urlsplit(url))
        host = parsed_url[1]
        parsed_url[1] = str(ip)
        newurl = urllib.parse.urlunsplit(parsed_url)
        req = urllib.request.Request(newurl)
        req.add_header('Host', host)
    else:
        req = urllib.request.Request(url)

    if proxy:
        req.set_proxy(proxy, 'http')
    
    req.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:30.0) Gecko/20100101 Firefox/30.0')

    try:
        opened = urllib.request.urlopen(req, timeout=15)
    except:
        return (0, '')
    return (opened.status, str(opened.readall()))

def test_dns():
    sites = {"gelbooru.com": '208.100.25.82'}
    sites_list = list(sites.keys())
    
    print("[O] Тестируем DNS")
    resolved_default_dns = _get_a_records(sites_list)
    print("\tАдреса через системный DNS:\t", str(resolved_default_dns))
    resolved_google_dns = _get_a_records(sites_list, '8.8.4.4')
    if resolved_google_dns != "":
        print("\tАдреса через Google DNS:\t", str(resolved_google_dns))
    else:
        print("\tНе удалось подключиться к Google DNS")
    resolved_az_dns = _get_a_records(sites_list, '107.150.11.192')
    if resolved_az_dns != "":
        print("\tАдреса через DNS AntiZapret:\t", str(resolved_az_dns))
    else:
        print("\tНе удалось подключиться к DNS AntiZapret")

    if (resolved_google_dns == "") & (resolved_google_dns == ""):
        return 4

    if resolved_default_dns == resolved_google_dns:
        if resolved_az_dns != resolved_default_dns:
            print("[✓] DNS записи не подменяются")
            print("[✓] DNS не перенаправляется")
            return 0
        elif resolved_az_dns == resolved_default_dns:
            if resolved_default_dns == list(sites.values()):
                print("[✓] DNS записи не подменяются")
                print("[☠] DNS перенаправляется")
                return 1
            else:
                print("[☠] DNS записи подменяются")
                print("[☠] DNS перенаправляется")
                return 2
    else:
        print("[☠] DNS записи подменяются")
        print("[✓] DNS не перенаправляется")
        return 3

def test_http_access(by_ip = False):
    sites = {'http://gelbooru.com/':
                 {'status': 200, 'lookfor': 'Hentai and Anime Imageboard', 'ip': '208.100.25.82'},
             'http://gelbooru.com/index.php?page=post&s=view&id=1989610':
                 {'status': 200, 'lookfor': 'Gelbooru- Image View', 'ip': '208.100.25.82'},
            }
    proxy = 'proxy.antizapret.prostovpn.org:3128'
    
    print("[O] Тестируем HTTP")

    siteresults = []
    for site in sites:
        print("\tОткрываем ", site)
        result = _get_url(site, ip=sites[site].get('ip') if by_ip else None)
        if result[0] == sites[site]['status'] and result[1].find(sites[site]['lookfor']) != -1:
            print("[✓] Сайт открывается")
            siteresults.append(True)
        else:
            print("[☠] Сайт не открывается")
            siteresults.append(False)

    siteresults_proxy = []
    for site in sites:
        print("\tОткрываем через прокси ", site)
        result_proxy = _get_url(site, proxy)
        if result_proxy[0] == sites[site]['status'] and result_proxy[1].find(sites[site]['lookfor']) != -1:
            print("[✓] Сайт открывается")
            siteresults_proxy.append(True)
        else:
            print("[☠] Сайт не открывается")
            siteresults_proxy.append(False)

    if all(siteresults):
        # No blocks
        return 0
    elif any(siteresults) and all(siteresults_proxy):
        # IP-DPI
        return 1
    elif any(siteresults) and any(siteresults_proxy):
        # Full-DPI
        return 2
    else:
        # IP
        return 3

def main():
    dns = test_dns()
    print()
    if dns == 0:
        http = test_http_access(False)
    else:
        http = test_http_access(True)
    print()
    print("[!] Результат:")
    if dns == 4:
        print("[⚠] Ваш провайдер блокирует чужие DNS-серверы.\n",
              "Вам следует использовать шифрованный канал до DNS-серверов, например, через VPN, Tor или " + \
              "HTTPS/Socks прокси.")
    elif dns == 3:
        print("[⚠] Ваш провайдер подменяет DNS-записи, но не перенаправляет чужие DNS-серверы на свой.\n",
              "Вам поможет смена DNS, например, на Яндекс.DNS 77.88.8.8 или Google DNS 8.8.8.8 и 8.8.4.4.")
    elif dns == 2:
        print("[⚠] Ваш провайдер подменяет DNS-записи и перенаправляет чужие DNS-серверы на свой.\n",
              "Вам следует использовать шифрованный канал до DNS-серверов, например, через VPN, Tor или " + \
              "HTTPS/Socks прокси.")
    elif dns == 1:
        print("[⚠] Ваш провайдер перенаправляет чужие DNS-серверы на свой, но не подменяет DNS-записи.\n",
              "Это несколько странно и часто встречается в мобильных сетях.\n",
              "Вам следует использовать шифрованный канал до DNS-серверов, например, через VPN, Tor или " + \
              "HTTPS/Socks прокси.")

    if http == 3:
        print("[⚠] Ваш провайдер блокирует по IP-адресу.\n",
              "Используйте любой способ обхода блокировок.")
    elif http == 2:
        print("[⚠] У вашего провайдера \"полный\" DPI. Он отслеживает ссылки даже внутри прокси, поэтому вам следует " + \
              "использовать любое шифрованное соединение, например, VPN или Tor.")
    elif http == 1:
        print("[⚠] У вашего провайдера \"обычный\" DPI.\n",
              "Вам поможет HTTPS/Socks прокси, VPN или Tor.")
    elif http == 0:
        print("[☺] Ваш провайдер не блокирует сайты.")

    _get_url('http://blockcheck.antizapret.prostovpn.org/index.php?dns=' + str(dns) + '&http=' + str(http))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Определитель типа блокировки сайтов у провайдера.')
    parser.add_argument('--console', action='store_true', help='Консольный режим. Отключает Tkinter GUI.')
    args = parser.parse_args()
    if args.console:
        tkusable = False

    if tkusable:
        root = tk.Tk()
        root.title("BlockCheck")
        text = ThreadSafeConsole(root)
        text.pack()
        threading.Thread(target=main).start()
        root.mainloop()
    else:
        main()
