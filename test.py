from io import StringIO
import os
import paramiko

ssh_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA46Xf1/1RclWWKIe79x3hhViq/SjT8nvDTps8aHAk0Ue5J3nu
/bWIimEMcKCnuTgPHLrpybPuUi91TzF7lddSACN+i6qFw2PArfJ+VUQdj8mc2Kx8
1GSdU1cC+EDUHMbbw9OLN3OxN5x2qKDa/a0hS6F9jFHKC1Murn4GBEKAcFbuIM6o
SeO6k3hjlzCA+f/mT50WWw6pH21ajnszjt00n59pooNbwBbi7clo+KKoa+8hKKRQ
lBhhgraMInY/Jky1RONnN+M8XA0nptWDNjzVk+TAFQeiz3HK5ll+6ZCEA7y0f7bf
7G85R3kcB/gd5U5cVVrWZ0PSBfqTcxHZPJZn3QIDAQABAoIBAB4z6LHoWwD3V/fC
om6T2VLuw6jY3N3kC7KHKAmXL1tQz8DsDYg9qILrg1ICDp6lUGP4bIIlTC49O6wp
HYNw0OFR1D1Ff3+/4VVywc4gPmfQUO3yXJF1U+Y1uiAjwcCbpZain2rY/58oNBoF
VWioqq01HMocI9lCzQO7lqLEC/RbZBPS2fNWL29PFgTAj1orJBLvkcvdkmOKbJcm
zboZ1kW5JsIEkqVuhjb0k+VIQW64rIuO3/IPKBanSBQnjtDuBXYZq8xl6TAPK0pp
YJ51CeUssmpUm/L+DSYHsLtyL9zufBLZNc+fC1KYR00A19rRx/KdwmqBdFwOh7f2
cRNfzaUCgYEA/aB9pFJsWPVzG86QbmDTBrf2KGVV8ys2QvYPsrpiCrWhuG8trHml
7Sqinl5fJnTa6Nb37rm50Vd+SHV85kf4xhbSD15enfq4tSnFMz7++S0iFtEVIzmk
F2jvyX+NXCSOPkoQMzZQsd33T8h6/5C0TIzuC0Qpc7Zpmne1EGilEFMCgYEA5cco
EWqNSwVCVXqlMUj9WLci45ziL/WLrP9lrWD9/nDab4oXVgGZsGHhbhHiCG2rR7Xh
3SiuwmcfsCDAYJjv92uRkSRl7DJjc9Nl5mQR88Wxr2N6qQ0xEH7UtWj79nbbhdzu
75Rh+5KAmAJcy4yF9aBkZspPIf+EJHQZp7X5YQ8CgYEAurYJiIy9Aog/IztgDEHv
WETZTEe9jHRFT+pBCDw5rNSlp1cBcrVjN0Npz9h9h5wDA+ItR2smpjwY1VLYjdZy
B7IJFhNM6FQI4iVL7Tv1DI7zR4TIYNQwPqOb0uS5thmbNbPkVS8pHKfhRrS6B6YJ
dUlSfKzDL1IcUADMJLZEvc0CgYA/k2QVtYqUiEb7SaztPwnCAyHnImA+7syPuDaU
yzJbtTPrCqU8ScMRV3O9Nbt5o4Zxl/R/caMw7MGKxPUVhRtYNO4Y355HxQVZZdNa
9LM25KsuIPMuVRUPQFhwPTUB048XsbJ2nXKi3b0w0e6E70OdW5yMCEvu1zjjsS/s
BGCUpwKBgQDN11GnoIp3k5pLfY8y5X/6RvIyy1EOqSPeNfDrH+X8h0cck5vPwzYg
Up9IrqzboZs+i86l9xFAyZj/s7VFxHssCl87IxmfbKOyH8KjSe9sJdTfndp+nyFo
bTLeUAiD0ZHMYKv1WX0l0UiImY/thA3vVkJnbT+qWOgJVkRaxUIk1A==
-----END RSA PRIVATE KEY-----"""
public_ip = "54.175.168.101"
username = "ubuntu"
key_stream = StringIO(ssh_key)
pkey = paramiko.RSAKey.from_private_key(key_stream)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Convert IP address format for AWS hostname
formatted_ip = public_ip.replace('.', '-')
hostname = f"ec2-{formatted_ip}.compute-1.amazonaws.com"

ssh.connect(hostname, username=username, pkey=pkey)

# Create an /home/ec2-user/app directory
sftp = ssh.open_sftp()
try:
    sftp.mkdir(f"/home/{username}/apptest")
except IOError:
    pass  # directory may already exist

print("Directory created successfully.")

sftp.close()