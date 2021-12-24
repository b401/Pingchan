from app import app
from app.database import db,PingCastle,APICastle

def xml_to_html(xml_path,api) -> bool:
    import os.path
    from os import remove
    import subprocess
    from pprint import pprint
    if (entry := PingCastle.query.filter_by(apikey=api).first()) is not None:
        print("Entry found!")
        key = entry.privatekey
        try:
            output = subprocess.run([f"{app.config['PINGCASTLE_FOLDER']}decryptor/decryptor", xml_path, key],cwd=app.config['UPLOAD_FOLDER'], capture_output=True)
            print(f"Decryptor: {output.returncode}")
            if output.returncode == 0:
                print("Could decrypt xml")
                filename = os.path.basename(xml_path)
                output = subprocess.run(['mono',f"{app.config['PINGCASTLE_FOLDER']}src/PingCastle.exe",'--regen-report', f"{app.config['UPLOAD_FOLDER']}ad_hc_{filename}"],cwd=app.config['REPORT_FOLDER'], capture_output=True)
                if output.returncode == 0:
                    # Remove api and private key
                    db.session.delete(entry)
                    db.session.commit()
                    return True
            else:
                print("Could not decrypt XML")
                return False
        except Exception as E:
            print(E)
            return False
    else:
        print(f"Key: {api} not found!!")
        return False

def generate_keys(name):
    import subprocess
    from pprint import pprint
    name = clean_path(name)

    try:
        keys = subprocess.run(['mono',f"{app.config['PINGCASTLE_FOLDER']}src/PingCastle.exe",'--generate-key'],cwd=app.config['PINGCASTLE_FOLDER'], capture_output=True)
    except Exception as e:
        raise Exception(f"Could not run subprocess: {e}")
    private_key, public_key = extract_rsa_keys(keys.stdout)
    api_key = generate_random_key(128)
    write_xml_config(public_key)
    save_keys(private_key, name, api_key)

    return api_key
    

def extract_rsa_keys(unclean_keypair):
    import re
    from pprint import pprint
    unclean_keypair_string = unclean_keypair.decode()
    regex_pub = 'publicKey=\"(.*)\"' 
    regex_pri = 'privateKey=\"(.*)\"' 

    public_key = re.search(regex_pub, unclean_keypair_string).group(1)
    private_key = re.search(regex_pri, unclean_keypair_string).group(1)
    return (private_key, public_key)
    
    

def generate_random_key(length):
    from random import choice
    from string import hexdigits

    return ''.join(choice(hexdigits) for i in range(length))

def temporarily_save_api(ip,api_key):
    try:
        new_entry = APICastle(ip=ip,apikey=api_key)
        db.session.add(new_entry)
        db.session.commit()
    except Exception as e:
        print(f"ERROR: {e}")
    print("Added new entry to database")
    return True

def get_api_key_from_ip(ip):
    if(entry := APICastle.query.filter_by(ip=ip).first()) is not None:
        db.session.delete(entry)
        db.session.commit()
        return entry.apikey
    else:
        return None

def check_api_login(key):
    if(entry := PingCastle.query.filter_by(apikey=key).first()) is not None:
        return True
    else:
        return None

    
    

def save_keys(private_key, name, api_key):
    import os.path
    import html

    ## check if name already exist and remove entry
    if(entry := PingCastle.query.filter_by(name=name).first()) is not None:
        db.session.delete(entry)
        db.session.commit()
        
    
    try:
        html_decoded_private_key = html.unescape(private_key)
        new_entry = PingCastle(name=name, privatekey=html_decoded_private_key, apikey=api_key)
        db.session.add(new_entry)
        db.session.commit()
    except Exception as e:
        raise Exception(f"Error saving key to database: {e}")

    return True
    
    

# If the function gets called with public=True only the public key gets included in the xml.
# public=False generates the decryption configuration
def write_xml_config(key=None ,api=None):
    import xml.etree.ElementTree as ET
    import shutil


    configuration = ET.Element('configuration')
    configSections = ET.SubElement(configuration,'configSections')
    section1 = ET.SubElement(configSections,'section', attrib={'name': 'LicenseSettings', 'type':'PingCastle.ADHealthCheckingLicenseSettings, PingCastle'})
    section2 = ET.SubElement(configSections,'section', attrib={'name': 'encryptionSettings', 'type':'PingCastle.Healthcheck.EncryptionSettings, PingCastle'})
    startup = ET.SubElement(configuration, 'startup', attrib={'useLegacyV2RuntimeActivationPolicy': 'true'})
    supportedRuntime = ET.SubElement(startup,'supportedRuntime', attrib={'version':'v4.0'})
    supportedRuntime2 = ET.SubElement(startup,'supportedRuntime', attrib={'version':'v2.0.50727'})
    liceensesettings = ET.SubElement(configuration, 'LicenseSettings', attrib={'license': ''})
    encryptionsettings = ET.SubElement(configuration, 'encryptionSettings', attrib={'encryptionKey': 'default'})
    rsakeys = ET.SubElement(encryptionsettings, 'RSAKeys')
    keysettings = ET.SubElement(rsakeys, 'KeySettings', attrib={'name':'default','publicKey': key})
    path = f"{app.config['PINGCASTLE_FOLDER']}src/PingCastle.exe.config"
    tree = ET.ElementTree(configuration)
    tree.write(path,encoding='utf-8', xml_declaration=True, method='xml')

    # Damn etree replaces all & with &amp;
    # https://github.com/python/cpython/blob/main/Lib/xml/etree/ElementTree.py#L1033
    with open(path,'r') as f:
        xml_wrongly_formatted = f.read()
    with open(f"{path}.new",'a+') as new_f:
        if "&amp;" in xml_wrongly_formatted:
            new_f.write(xml_wrongly_formatted.replace('&amp;','&'))
    shutil.move(f"{path}.new",path)
    
    
def generate_download_link(path,api):
    if (entry := PingCastle.query.filter_by(apikey=api).first()) is not None:
        download_url = generate_random_key(8)
        entry.link = download_url
        entry.filepath = path
        db.session.commit()
        return download_url

def get_download_package(key):
    if (entry := PingCastle.query.filter_by(link=key).first()) is not None:
        return entry.filepath
    

def create_package(output_filename, cmd, api):
    import shutil
    clear_package()


    cmd = clean_path(cmd,'cmd')
    src_path = f"{app.config['PINGCASTLE_FOLDER']}src/"
    path = f"{app.config['PINGCASTLE_FOLDER']}output/{output_filename}"
    try:
        with open(f"{src_path}{output_filename}.ps1",'w') as a:
            a.write(f'''
Try {{
    Invoke-WebRequest -UseBasicParsing "https://{app.config['DOMAIN_NAME']}" -ErrorAction SilentlyContinue | Out-Null
    & .\PingCastle.exe {cmd} --api-key {api}
    Write-Host -ForegroundColor Green "All done."
    Write-Host -ForegroundColor Green "Report was automatically sent. Nothing to do here for you. :)"
}} catch {{
    & .\PingCastle.exe --healthcheck
    Write-Host -ForegroundColor Green "All done."
    Write-Host -ForegroundColor Green "Please send the generated html back :)"
}}

Write-Host -ForegroundColor Green "Thank you very much for your cooperation"
pause
''')
        shutil.make_archive(path, 'zip', src_path)
        return True
    except Exception as e:
        print(e)
        return False

def calculate_hash(filepath):
    import hashlib
    path = f"{app.config['PINGCASTLE_FOLDER']}output/{filepath}"
    with open(path,'rb') as f:
        r_bytes = f.read()
        zip_hash = hashlib.sha256(r_bytes).hexdigest()
        return zip_hash

def clear_package():
    import os
    path = f"{app.config['PINGCASTLE_FOLDER']}src"
    for item in os.listdir(path):
        if item.endswith(".ps1"):
            os.remove(os.path.join(path,item))


def clean_path(path,method="path") -> str:
    BLACKLIST = ['(',')','`',';','.','\\','/','%','@','$',':',"'",'"']
    if method == 'cmd':
        BLACKLIST = ['(',')','`',';','\\','%','@','$']
    return path.translate({ord(i): None for i in BLACKLIST})


def gen_reportlist():
    import fnmatch, os
    from pprint import pprint
    from datetime import datetime
    flist = {}
    for _, _, files in os.walk(app.config['REPORT_FOLDER']):
        for items in fnmatch.filter(files,"*.html"):
            try:
                mtime = os.path.getmtime(app.config['REPORT_FOLDER'] + items)
                modification_date = str(datetime.fromtimestamp(mtime).replace(microsecond=0))
                zone = os.path.splitext(items)[0]
                flist[zone] = {'report':items, 'date':modification_date}
            except Exception as e:
                print(e)
                pass
    return flist
